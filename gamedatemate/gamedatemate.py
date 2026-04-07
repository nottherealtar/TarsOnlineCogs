"""
Game Date Mate — forwards Discord presence to the Game Date Mate web app (Red-DiscordBot cog).

Sends rich presence (RPC details/state/party/timestamps/assets), all activity summaries,
guild nickname + username, and voice channel name so the web UI stays accurate.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("red.nottherealtar.gamedatemate")

# Coalesce rapid Discord events into one HTTP call per member (presence spams updates).
_DEBOUNCE_S = 1.0
# Space out bulk sync so the web app / host is not hammered.
_SYNC_DELAY_S = 0.06


def _normalize_base_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    parsed = urlparse(u)
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _safe_url(prop_getter, max_len: int = 2048) -> Optional[str]:
    try:
        u = prop_getter()
        if not u:
            return None
        s = str(u).strip()
        return s[:max_len] if s else None
    except Exception:
        return None


def _pick_primary_activity(member: discord.Member) -> Optional[discord.BaseActivity]:
    """Prefer playing/streaming/competing (game + RPC), then custom status, else first activity."""
    acts = list(member.activities or [])
    if not acts:
        return None
    priority = (
        discord.ActivityType.playing,
        discord.ActivityType.streaming,
        discord.ActivityType.competing,
    )
    for t in priority:
        for a in acts:
            if getattr(a, "type", None) == t:
                return a
    for a in acts:
        if getattr(a, "type", None) == discord.ActivityType.custom:
            return a
    return acts[0]


def _activity_display(activity: Optional[discord.BaseActivity]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Human label, ActivityType name, large art URL (game / rich presence asset)."""
    if activity is None:
        return None, None, None
    atype = getattr(activity, "type", None)
    type_str = atype.name.upper() if atype is not None and hasattr(atype, "name") else None
    name = getattr(activity, "name", None) or None

    if atype == discord.ActivityType.custom and name:
        label = name
    elif atype == discord.ActivityType.listening and name:
        label = f"Listening to {name}"
    elif atype == discord.ActivityType.watching and name:
        label = f"Watching {name}"
    elif atype == discord.ActivityType.streaming and name:
        label = f"Streaming {name}"
    elif name:
        label = name
    else:
        label = type_str.replace("_", " ").title() if type_str else None

    game_image = _safe_url(lambda: getattr(activity, "large_image_url", None))

    return label, type_str, game_image


def _party_to_rpc(party: Any) -> tuple[Optional[int], Optional[int]]:
    if party is None:
        return None, None
    if isinstance(party, (list, tuple)) and len(party) >= 2:
        try:
            return int(party[0]), int(party[1])
        except (TypeError, ValueError):
            return None, None
    size = getattr(party, "size", None)
    if isinstance(size, (list, tuple)) and len(size) >= 2:
        try:
            return int(size[0]), int(size[1])
        except (TypeError, ValueError):
            return None, None
    return None, None


def _dt_iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return None


def _rpc_from_activity(activity: Optional[discord.BaseActivity]) -> dict[str, Any]:
    if activity is None:
        return {}
    rpc: dict[str, Any] = {}
    for attr, key, maxlen in (("details", "details", 600), ("state", "state", 600)):
        v = getattr(activity, attr, None)
        if v:
            rpc[key] = str(v)[:maxlen]
    pc, pm = _party_to_rpc(getattr(activity, "party", None))
    if pc is not None and pm is not None and pm > 0:
        rpc["partyCurrent"] = pc
        rpc["partyMax"] = pm
    rpc["startedAt"] = _dt_iso(getattr(activity, "start", None))
    rpc["endsAt"] = _dt_iso(getattr(activity, "end", None))
    liu = _safe_url(lambda: getattr(activity, "large_image_url", None))
    siu = _safe_url(lambda: getattr(activity, "small_image_url", None))
    if liu:
        rpc["largeImageUrl"] = liu
    if siu:
        rpc["smallImageUrl"] = siu
    for attr, key, maxlen in (("large_text", "largeText", 200), ("small_text", "smallText", 200)):
        v = getattr(activity, attr, None)
        if v:
            rpc[key] = str(v)[:maxlen]
    url = getattr(activity, "url", None)
    if url:
        rpc["streamUrl"] = str(url).strip()[:2048]
    emoji = getattr(activity, "emoji", None)
    if emoji is not None:
        ed: dict[str, Any] = {"animated": bool(getattr(emoji, "animated", False))}
        en = getattr(emoji, "name", None)
        if en:
            ed["name"] = str(en)[:100]
        eid = getattr(emoji, "id", None)
        if eid:
            ed["id"] = str(eid)
        rpc["emoji"] = ed
    return rpc


def _activities_summary(member: discord.Member) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for a in (member.activities or [])[:8]:
        t = getattr(getattr(a, "type", None), "name", None) or "unknown"
        n = getattr(a, "name", None) or ""
        if not str(n).strip() and not str(t).strip():
            continue
        out.append({"type": str(t).upper()[:32], "name": str(n).strip()[:200] or t.upper()})
    return out


def _member_labels(member: discord.Member) -> dict[str, Any]:
    labels: dict[str, Any] = {
        "displayName": member.display_name[:100] if member.display_name else None,
        "userName": member.name[:100] if member.name else None,
    }
    gn = getattr(member, "global_name", None)
    if gn:
        labels["globalName"] = str(gn)[:100]
    else:
        labels["globalName"] = None
    return labels


def _member_presence_payload(guild: discord.Guild, member: discord.Member) -> dict[str, Any]:
    activity = _pick_primary_activity(member)
    act_label, act_type, game_image = _activity_display(activity)
    voice_ch = member.voice.channel if member.voice else None
    rpc = _rpc_from_activity(activity)
    snapshot: dict[str, Any] = {"member": _member_labels(member)}
    if rpc:
        snapshot["rpc"] = rpc
    summary = _activities_summary(member)
    if summary:
        snapshot["activitiesSummary"] = summary

    payload: dict[str, Any] = {
        "guildId": str(guild.id),
        "discordUserId": str(member.id),
        "status": member.status.name if member.status else "offline",
        "activity": act_label,
        "activityType": act_type,
        "gameImage": game_image,
        "inVoice": voice_ch is not None,
        "voiceChannelId": str(voice_ch.id) if voice_ch else None,
        "voiceChannelName": voice_ch.name[:100] if voice_ch and voice_ch.name else None,
        "discordSnapshot": snapshot,
    }
    return payload


def _member_identity_changed(before: discord.Member, after: discord.Member) -> bool:
    if before.display_name != after.display_name or before.name != after.name:
        return True
    bg = getattr(before, "global_name", None)
    ag = getattr(after, "global_name", None)
    return bg != ag


class GameDateMate(commands.Cog):
    """Sync member presence to **Game Date Mate** so your group can see who is playing what.

    **Quick setup (server admins):** run ``/gamedatemate guide`` (or ``[p]gamedatemate guide``).

    The bot needs **Server Members Intent** and **Presence Intent** enabled in the Discord Developer Portal
    and loaded on your Red instance (e.g. ``[p]set intents``).
    """

    __author__ = ["nottherealtar"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210, force_registration=True)
        self.config.register_guild(enabled=False, app_url="", secret="")
        self._http: Optional[aiohttp.ClientSession] = None
        self._debounce_tasks: dict[str, asyncio.Task] = {}

    async def cog_load(self) -> None:
        # One pooled session: avoids new TLS + TCP per presence tick (major reliability win on busy guilds).
        self._http = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": "GameDateMate-RedCog/2.0 (+https://github.com/nottherealtar/TarsOnlineCogs)"},
        )

    async def cog_unload(self) -> None:
        for t in list(self._debounce_tasks.values()):
            if not t.done():
                t.cancel()
        self._debounce_tasks.clear()
        if self._http and not self._http.closed:
            await self._http.close()
        self._http = None

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def red_delete_data_for_guild(self, *, guild_id: int):
        await self.config.guild_from_id(guild_id).clear()

    def _intents_ok(self) -> tuple[bool, list[str]]:
        missing = []
        if not self.bot.intents.members:
            missing.append("members")
        if not self.bot.intents.presences:
            missing.append("presences")
        return (len(missing) == 0, missing)

    async def _guild_ready(self, guild: discord.Guild) -> bool:
        if not await self.config.guild(guild).enabled():
            return False
        url = _normalize_base_url(await self.config.guild(guild).app_url())
        secret = (await self.config.guild(guild).secret() or "").strip()
        return bool(url and secret)

    async def _post_presence_now(self, guild: discord.Guild, member: discord.Member) -> tuple[int, str]:
        """Send one payload; returns (status_code, response_snippet)."""
        if member.bot:
            return 0, "skipped_bot"
        if not await self._guild_ready(guild):
            return 0, "skipped_guild_disabled"
        if self._http is None or self._http.closed:
            log.error("GameDateMate: HTTP session not ready — reload the cog or restart Red.")
            return 0, "no_session"
        url = _normalize_base_url(await self.config.guild(guild).app_url())
        secret = (await self.config.guild(guild).secret() or "").strip()
        payload = _member_presence_payload(guild, member)
        endpoint = f"{url}/api/discord/presence"
        try:
            async with self._http.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "x-gdm-secret": secret,
                },
                json=payload,
            ) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    log.warning(
                        "GameDateMate POST %s -> %s: %s",
                        resp.status,
                        endpoint,
                        text[:500],
                    )
                elif resp.status == 200:
                    try:
                        j = json.loads(text) if text else {}
                        sk = j.get("skipped")
                        if sk:
                            log.info(
                                "GameDateMate OK but app skipped discordUserId=%s reason=%s "
                                "(link Discord in Clerk + join the group on the site)",
                                member.id,
                                sk,
                            )
                    except Exception:
                        pass
                return resp.status, text[:800]
        except aiohttp.ClientError as e:
            log.warning("GameDateMate POST failed: %s", e)
            return 0, str(e)[:400]

    def _schedule_presence_post(self, guild: discord.Guild, member: discord.Member) -> None:
        """Debounce: Discord can emit many presence updates per second for one user."""
        if member.bot:
            return
        key = f"{guild.id}-{member.id}"
        old = self._debounce_tasks.pop(key, None)
        if old is not None and not old.done():
            old.cancel()
        mid = member.id
        gid = guild.id

        async def _run() -> None:
            try:
                await asyncio.sleep(_DEBOUNCE_S)
                g = self.bot.get_guild(gid)
                if g is None:
                    return
                m = g.get_member(mid)
                if m is None or m.bot:
                    return
                await self._post_presence_now(g, m)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("GameDateMate debounced post failed guild=%s member=%s", gid, mid)
            finally:
                self._debounce_tasks.pop(key, None)

        self._debounce_tasks[key] = asyncio.create_task(_run())

    async def _post_presence(self, guild: discord.Guild, member: discord.Member) -> None:
        self._schedule_presence_post(guild, member)

    @commands.Cog.listener()
    async def on_presence_update(self, before: Optional[discord.Member], after: Optional[discord.Member]):
        # discord.py: (before, after) are both Member for the same user.
        if after is None or after.guild is None:
            return
        self._schedule_presence_post(after.guild, after)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild
        if before.channel == after.channel:
            return
        # Voice moves should feel snappy — post soon but still coalesce double events.
        self._schedule_presence_post(guild, member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Push new nickname / username labels when they change (presence event may not fire)."""
        if after.guild is None:
            return
        if not _member_identity_changed(before, after):
            return
        self._schedule_presence_post(after.guild, after)

    @commands.hybrid_group(name="gamedatemate", aliases=["gdm"], invoke_without_command=True, fallback="help")
    @commands.guild_only()
    async def gamedatemate(self, ctx: commands.Context):
        """Game Date Mate: link this Discord server to your web app for live presence."""
        p = ctx.clean_prefix
        embed = discord.Embed(
            title="Game Date Mate",
            description=(
                f"Use **`{p}gamedatemate`** or **`/gamedatemate`**.\n"
                "Start with **`guide`** for a full checklist, or **`status`** to see how you’re configured."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Main commands",
            value=(
                f"`{p}gamedatemate guide` — setup walkthrough\n"
                f"`{p}gamedatemate url` / `secret` / `enable` / `disable`\n"
                f"`{p}gamedatemate status` — config + intents\n"
                f"`{p}gamedatemate test` — reachability check\n"
                f"`{p}gamedatemate push` — send **your** presence now (see API reply)\n"
                f"`{p}gamedatemate sync` — backfill **all** cached members (admin)"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @gamedatemate.command(name="guide")
    @commands.bot_has_permissions(embed_links=True)
    @commands.has_permissions(manage_guild=True)
    async def gdm_guide(self, ctx: commands.Context):
        """Step-by-step setup in one message."""
        ok, missing = self._intents_ok()
        intent_line = (
            "✅ Bot intents look good (members + presences)."
            if ok
            else f"⚠️ Enable these bot intents: **{', '.join(missing)}** — Discord Developer Portal → Bot → Privileged Gateway Intents, then reload/restart Red."
        )
        embed = discord.Embed(
            title="Game Date Mate — setup guide",
            description=(
                "Link this server to your **Game Date Mate** web app so group members see who is online, "
                "what they are playing (including rich presence), and voice channel names."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="1. Discord Developer Portal",
            value=(
                "Open your bot application → **Bot** → enable **Presence Intent** and **Server Members Intent**. "
                "On Red, ensure those intents are on (e.g. `[p]set intents`)."
            ),
            inline=False,
        )
        embed.add_field(
            name="2. Web app (group admin)",
            value=(
                "In Game Date Mate → your group **Settings**, set **Discord server ID** to this guild’s ID "
                f"(`{ctx.guild.id}`). Users must link Discord accounts on the site to appear in presence."
            ),
            inline=False,
        )
        embed.add_field(
            name="3. Connect this server to the API",
            value=(
                "Use the same **base URL** as your deployed app (e.g. `https://your-app.vercel.app`) and the "
                "**DISCORD_BOT_WEBHOOK_SECRET** value from your hosting env.\n"
                "• `/gamedatemate url <url>`\n"
                "• `/gamedatemate secret <secret>` (slash replies are ephemeral)\n"
                "• `/gamedatemate enable`"
            ),
            inline=False,
        )
        embed.add_field(
            name="4. Check it",
            value="`/gamedatemate status` — then change game, rich presence, or join voice; registered members update in the app.",
            inline=False,
        )
        embed.set_footer(text=intent_line)
        await ctx.send(embed=embed)

    @gamedatemate.command(name="url")
    @commands.has_permissions(manage_guild=True)
    async def gdm_url(self, ctx: commands.Context, base_url: str):
        """Set your Game Date Mate site base URL (no trailing path)."""
        normalized = _normalize_base_url(base_url)
        if not normalized:
            await ctx.send("That doesn’t look like a valid URL. Example: `https://my-app.vercel.app`")
            return
        await self.config.guild(ctx.guild).app_url.set(normalized)
        await ctx.send(f"Saved base URL: `{normalized}`\nNext: `/gamedatemate secret …` then `/gamedatemate enable`.")

    @gamedatemate.command(name="secret")
    @commands.has_permissions(manage_guild=True)
    async def gdm_secret(self, ctx: commands.Context, webhook_secret: str):
        """Set the webhook secret (must match DISCORD_BOT_WEBHOOK_SECRET on the app)."""
        secret = (webhook_secret or "").strip()
        if len(secret) < 8:
            await ctx.send("That secret looks too short. Copy the full value from your app’s environment variables.")
            return
        await self.config.guild(ctx.guild).secret.set(secret)
        msg = "Webhook secret saved for this server."
        if ctx.interaction:
            await ctx.send(msg, ephemeral=True)
        else:
            await ctx.send(f"{msg}\nIf you typed this in a public channel, delete your message for safety.")

    @gamedatemate.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def gdm_enable(self, ctx: commands.Context):
        """Turn on presence forwarding for this server."""
        url = _normalize_base_url(await self.config.guild(ctx.guild).app_url())
        secret = (await self.config.guild(ctx.guild).secret() or "").strip()
        if not url or not secret:
            await ctx.send("Set **url** and **secret** first. Use `/gamedatemate guide` for steps.")
            return
        ok, missing = self._intents_ok()
        if not ok:
            await ctx.send(
                f"Bot is missing intents: **{', '.join(missing)}**. Fix in the Developer Portal and Red, then try again."
            )
            return
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Game Date Mate presence sync is **on** for this server.")

    @gamedatemate.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def gdm_disable(self, ctx: commands.Context):
        """Stop forwarding presence from this server."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Game Date Mate presence sync is **off** for this server.")

    @gamedatemate.command(name="status")
    @commands.has_permissions(manage_guild=True)
    async def gdm_status(self, ctx: commands.Context):
        """Show whether this server is configured and intents are OK."""
        enabled = await self.config.guild(ctx.guild).enabled()
        url = _normalize_base_url(await self.config.guild(ctx.guild).app_url())
        secret_set = bool((await self.config.guild(ctx.guild).secret() or "").strip())
        ok, missing = self._intents_ok()
        lines = [
            f"**Forwarding:** {'enabled' if enabled else 'disabled'}",
            f"**App URL:** `{url or 'not set'}`",
            f"**Webhook secret:** {'set' if secret_set else 'not set'}",
            f"**Intents:** {'OK' if ok else 'missing ' + ', '.join(missing)}",
            f"**This guild ID** (for the web app): `{ctx.guild.id}`",
        ]
        embed = discord.Embed(
            title="Game Date Mate — status",
            description="\n".join(lines),
            color=discord.Color.green() if (enabled and ok and url and secret_set) else discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    @gamedatemate.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def gdm_test(self, ctx: commands.Context):
        """Check that your app URL is reachable (does not send a fake presence)."""
        url = _normalize_base_url(await self.config.guild(ctx.guild).app_url())
        if not url:
            await ctx.send("Set the URL first: `/gamedatemate url …`")
            return
        probe = f"{url}/api/discord/presence"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    probe,
                    headers={"Content-Type": "application/json", "x-gdm-secret": "invalid-probe"},
                    json={"guildId": "0", "discordUserId": "0", "status": "online"},
                    timeout=aiohttp.ClientTimeout(total=12),
                ) as resp:
                    if resp.status == 401:
                        await ctx.send(
                            "✅ API is reachable — got **401** (expected with a wrong secret). "
                            "Your **secret** command should match `DISCORD_BOT_WEBHOOK_SECRET` exactly."
                        )
                        return
                    if resp.status == 404:
                        await ctx.send(
                            "⚠️ Got **404** on the presence route. Check the base URL (must be your deployed app root)."
                        )
                        return
                    text = await resp.text()
                    await ctx.send(f"Unexpected response **{resp.status}**: `{text[:200]}`")
        except aiohttp.ClientError as e:
            await ctx.send(f"Could not reach the app: `{e}`")

    @gamedatemate.command(name="push")
    async def gdm_push(self, ctx: commands.Context):
        """POST your current presence immediately and show the API response (troubleshooting)."""
        if ctx.guild is None:
            return
        if not await self._guild_ready(ctx.guild):
            await ctx.send("Enable forwarding for this server first (`/gamedatemate enable`).")
            return
        if ctx.author.bot:
            return
        status, snippet = await self._post_presence_now(ctx.guild, ctx.author)
        await ctx.send(
            f"**HTTP {status}** for your user `{ctx.author.id}`\n```\n{snippet}\n```\n"
            "• `skipped: user_not_registered` → link Discord in **Clerk** on the site.\n"
            "• `skipped: not_in_group` → join the group with an invite on the site.\n"
            "• `ok: true` → stored; refresh the Members page.",
            ephemeral=bool(ctx.interaction),
        )

    @gamedatemate.command(name="sync")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(read_messages=True)
    async def gdm_sync(self, ctx: commands.Context):
        """POST presence for every non-bot member currently in cache (fills gaps after bot restarts)."""
        if ctx.guild is None:
            return
        if not await self._guild_ready(ctx.guild):
            await ctx.send("Enable forwarding and set URL + secret first.")
            return
        guild = ctx.guild
        if ctx.interaction:
            await ctx.defer(ephemeral=False)
        msg = await ctx.send("Chunking members (if needed) and syncing presence to Game Date Mate…")
        try:
            if not guild.chunked:
                await guild.chunk(cache=True)
        except Exception as e:
            log.warning("GameDateMate sync chunk failed: %s", e)
        members = [m for m in guild.members if not m.bot]
        ok = 0
        err = 0
        for m in members:
            code, _ = await self._post_presence_now(guild, m)
            if code == 200:
                ok += 1
            elif code > 0:
                err += 1
            await asyncio.sleep(_SYNC_DELAY_S)
        await msg.edit(
            content=(
                f"Sync finished: **{ok}** HTTP 200, **{err}** other codes, **{len(members)}** members processed.\n"
                "200 + `skipped` in logs still means the web app ignored some users (not linked / not in group)."
            )
        )
