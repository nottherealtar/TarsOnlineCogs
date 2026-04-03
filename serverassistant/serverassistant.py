from redbot.core import commands, Config
import discord
from discord import app_commands
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import asyncio
import math
import re
from typing import Optional, Union

DISCORD_TIMEOUT_MAX = timedelta(days=28)


def _parse_duration_token(token: str) -> Optional[int]:
    """Parse ``10s``, ``5m``, ``2h``, ``1d`` into seconds. Caps at 28 days (Discord timeout limit)."""
    m = re.fullmatch(r"(\d+)([smhd])", token.strip().lower())
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    sec = n * mult[u]
    return min(sec, int(DISCORD_TIMEOUT_MAX.total_seconds()))


def _split_mute_reason(reason: str) -> tuple[Optional[int], Optional[str]]:
    """If *reason* starts with a duration token, return (seconds, rest). Otherwise (None, reason)."""
    reason = (reason or "").strip()
    if not reason:
        return None, None
    first, _, rest = reason.partition(" ")
    dur = _parse_duration_token(first)
    if dur is not None:
        return dur, rest.strip() or None
    return None, reason or None


def _emoji_key(emoji: discord.PartialEmoji | str) -> str:
    if isinstance(emoji, str):
        return emoji
    if emoji.id:
        return f"{emoji.name}:{emoji.id}"
    return emoji.name or ""


def _level_from_xp(xp: int) -> int:
    """``level = floor(sqrt(xp / 100))`` so early levels are quick, later ones stretch out."""
    return int(math.sqrt(max(0, xp) / 100.0))


def _xp_band(level: int) -> tuple[int, int]:
    """Min XP (inclusive) for *level*, and min XP for *level+1*."""
    low = int(level * level * 100)
    high = int((level + 1) ** 2 * 100)
    return low, high


def _xp_progress(xp: int) -> tuple[int, int, int]:
    """Current level, XP earned within this level, XP span of this level band."""
    lvl = _level_from_xp(xp)
    low, high = _xp_band(lvl)
    span = max(1, high - low)
    into = max(0, xp - low)
    return lvl, into, span

COLOR_ROLES = {
    "Warm": {
        "Red": discord.Color.red(),
        "Orange": discord.Color.orange(),
        "Yellow": discord.Color.gold(),
        "Gold": discord.Color.gold(),
        "Pink": discord.Color.magenta(),
    },
    "Cool": {
        "Blue": discord.Color.blue(),
        "Cyan": discord.Color.from_rgb(0, 255, 255),
        "Teal": discord.Color.teal(),
        "Indigo": discord.Color.from_rgb(75, 0, 130),
        "Violet": discord.Color.from_rgb(238, 130, 238),
        "Purple": discord.Color.purple(),
    },
    "Neutral": {
        "White": discord.Color.from_rgb(255, 255, 255),
        "Black": discord.Color.from_rgb(0, 0, 0),
        "Gray": discord.Color.from_rgb(128, 128, 128),
        "Silver": discord.Color.from_rgb(192, 192, 192),
        "Brown": discord.Color.from_rgb(139, 69, 19),
    },
    "Nature": {
        "Green": discord.Color.green(),
        "Lime": discord.Color.from_rgb(191, 255, 0),
    },
}


class ServerAssistant(commands.Cog):
    """Server utilities for public communities: moderation, light automation, member info, and optional anti-spam.

    Use ``[p]serverassistant`` (or ``/serverassistant``) for a full command list. Admins should set a **log** channel
    and review **antispam** before relying on it in production. Color roles require ``createcolorroles`` before the picker works.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654321, force_registration=True)
        default_guild = {
            "autorole": None,
            "log_channel": None,
            "antispam_enabled": False,
            "antispam_message_limit": 5,  # messages
            "antispam_time_window": 5,    # seconds
            "antispam_action": "mute",    # mute, kick, or warn
            "antispam_mute_duration": 300, # seconds (5 minutes)
            "colorpicker_channel": None,
            "colorpicker_message": None,
            "verify_button_roles": [],  # role IDs with persistent verify buttons (for restarts)
            # Leveling
            "leveling_enabled": False,
            "leveling_xp_min": 15,
            "leveling_xp_max": 25,
            "leveling_cooldown": 60,
            "leveling_ignored_channels": [],
            "leveling_ignored_roles": [],
            # Starboard
            "starboard_channel": None,
            "starboard_min": 3,
            "starboard_emoji": "\N{WHITE MEDIUM STAR}",  # ⭐
            "starboard_ignore_self": True,
            "starboard_posts": {},  # str(orig_msg_id) -> starboard message id
            # Reaction roles: str(msg_id) -> {emoji_key: role_id}
            "reaction_roles": {},
            # Role menus: str(msg_id) -> {"channel_id": int, "roles": [int, ...]}
            "role_menus": {},
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(xp=0, last_xp_at=0.0)

        # Anti-spam tracking: {guild_id: {user_id: [timestamps]}}
        self.message_cache = defaultdict(lambda: defaultdict(list))

        # Leveling cooldown in-memory {guild_id: {user_id: monotonic_ts}}
        self._level_cooldown = defaultdict(dict)

        # One bot.add_view per verification role ID (custom_id includes role id)
        self._verify_view_role_ids = set()
        self._role_menu_message_ids = set()

    async def cog_load(self):
        """Restore persistent UI components after a restart."""
        self.bot.add_view(ColorPickerView(self))
        for guild in self.bot.guilds:
            role_ids = await self.config.guild(guild).verify_button_roles()
            for rid in role_ids:
                if guild.get_role(rid):
                    self._register_verify_view(rid)
            menus = await self.config.guild(guild).role_menus()
            for mid_str, data in list(menus.items()):
                try:
                    mid = int(mid_str)
                    roles = data.get("roles") or []
                    ch_id = data.get("channel_id")
                    if ch_id and guild.get_channel(ch_id) and roles:
                        self._register_role_menu_view(guild, mid, roles, view=None)
                except (TypeError, ValueError):
                    continue

    def _register_verify_view(self, role_id: int) -> None:
        if role_id in self._verify_view_role_ids:
            return
        self._verify_view_role_ids.add(role_id)
        self.bot.add_view(VerifyView(self, role_id))

    def _register_role_menu_view(
        self,
        guild: discord.Guild,
        message_id: int,
        role_ids: list,
        view: Optional["RoleMenuView"] = None,
    ) -> None:
        if message_id in self._role_menu_message_ids:
            return
        self._role_menu_message_ids.add(message_id)
        self.bot.add_view(view or RoleMenuView(self, guild, message_id, role_ids))

    async def red_delete_data_for_user(self, **kwargs):
        """Remove stored leveling XP for this user in every guild the bot is in."""
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()

    async def _maybe_award_xp(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return
        guild = message.guild
        settings = await self.config.guild(guild).all()
        if not settings["leveling_enabled"]:
            return
        if message.channel.id in (settings["leveling_ignored_channels"] or []):
            return
        member = message.author
        if not isinstance(member, discord.Member):
            return
        ignored_roles = set(settings["leveling_ignored_roles"] or [])
        if ignored_roles and ignored_roles.intersection({r.id for r in member.roles}):
            return

        import time
        import random

        now = time.time()
        cd = max(5, int(settings["leveling_cooldown"]))
        last = self._level_cooldown[guild.id].get(member.id, 0.0)
        if now - last < cd:
            return
        self._level_cooldown[guild.id][member.id] = now

        lo = min(int(settings["leveling_xp_min"]), int(settings["leveling_xp_max"]))
        hi = max(int(settings["leveling_xp_min"]), int(settings["leveling_xp_max"]))
        gain = random.randint(lo, hi)
        cur = await self.config.member(member).xp()
        await self.config.member(member).xp.set(cur + gain)

    async def _get_or_create_muted_role(self, guild: discord.Guild) -> discord.Role:
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if muted_role:
            return muted_role
        muted_role = await guild.create_role(name="Muted", reason="ServerAssistant mute role")
        for ch in guild.channels:
            try:
                await ch.set_permissions(muted_role, send_messages=False, speak=False)
            except discord.Forbidden:
                pass
        return muted_role

    async def _delayed_remove_muted_role(
        self, guild: discord.Guild, member_id: int, muted_role: discord.Role, duration: int
    ) -> None:
        await asyncio.sleep(duration)
        try:
            member = guild.get_member(member_id)
            if member is None:
                try:
                    member = await guild.fetch_member(member_id)
                except discord.NotFound:
                    return
            if muted_role in member.roles:
                await member.remove_roles(muted_role, reason="Timed mute expired")
            await self._log_action(guild, f"[Mute] {member} — timed mute ({duration}s) expired.")
        except discord.Forbidden:
            await self._log_action(guild, f"[Mute] Could not remove Muted from <@{member_id}> — missing permissions.")
        except Exception as e:
            await self._log_action(guild, f"[Mute] Timed unmute error for <@{member_id}>: {e}")

    @staticmethod
    async def _apply_text_lock(channel: discord.abc.GuildChannel, guild: discord.Guild, locked: bool) -> None:
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(
                guild.default_role,
                send_messages=False if locked else None,
            )
        elif isinstance(channel, discord.ForumChannel):
            try:
                await channel.set_permissions(
                    guild.default_role,
                    send_messages=False if locked else None,
                    create_public_threads=False if locked else None,
                )
            except TypeError:
                await channel.set_permissions(
                    guild.default_role,
                    send_messages=False if locked else None,
                )

    @commands.hybrid_group(invoke_without_command=True, fallback="help")
    async def serverassistant(self, ctx):
        """ServerAssistant: moderation, automation, and server info (see subcommands)."""
        p = ctx.clean_prefix
        help_message = discord.Embed(
            title="ServerAssistant",
            description=(
                f"Prefix **`{p}`** or slash **`/serverassistant`** — same commands where marked hybrid.\n"
                "**Tip:** Set `{0}serverassistant log set #channel` so kicks, bans, verification, and anti-spam are recorded."
            ).format(p),
            color=discord.Color.blurple(),
        )
        help_message.add_field(
            name="Moderation & channels",
            value=(
                f"`{p}serverassistant kick` / `ban` / `mute` / `unmute` / `warn` / `purge` — usual Discord perms.\n"
                f"`{p}serverassistant mute @user 10m reason` — timed mute (timeout if possible, else **Muted** role).\n"
                f"`{p}serverassistant slowmode set 30` — optional `#channel`; `{p}serverassistant lock` / `unlock` (text/forum).\n"
                f"`{p}serverassistant lockcategory` / `unlockcategory` — bulk lock under a category.\n"
                f"`{p}serverassistant log` — `set` / `clear` mod log channel."
            ),
            inline=False,
        )
        help_message.add_field(
            name="Automation & safety",
            value=(
                f"`{p}serverassistant antispam` — view settings; subcommands: `enable`, `disable`, `limit`, `window`, `action`, `mutetime`.\n"
                f"`{p}serverassistant autorole` — `set` / `clear`; assigns a role on join.\n"
                f"`{p}serverassistant verifybutton` — posts a **persistent** Verify button (role optional; defaults to **Verified**)."
            ),
            inline=False,
        )
        help_message.add_field(
            name="Appearance & engagement",
            value=(
                f"`{p}serverassistant announce` / `announceembed` — plain or embed (+ optional `@here` / `@everyone`).\n"
                f"`{p}serverassistant poll` — up to 10 options.\n"
                f"`{p}serverassistant createcolorroles` + `colorpicker setup` — color roles.\n"
                f"`{p}serverassistant level` — XP card; `level enable`, `leaderboard`, `xprange`, `cooldown`, `ignorechannel`…\n"
                f"`{p}serverassistant starboard set #channel` — `minimum`, `emoji`, `selfstar`; ⭐ reposts.\n"
                f"`{p}serverassistant reactionrole add` (message + emoji + role) — classic reaction roles.\n"
                f"`{p}serverassistant rolemenu send` — **prefix** multi-select role menu (max 25 roles)."
            ),
            inline=False,
        )
        help_message.add_field(
            name="Information",
            value=(
                f"`{p}serverassistant userinfo` · `roleinfo` · `serverstats` · `channelmap` — who/what/where overview."
            ),
            inline=False,
        )
        help_message.set_footer(
            text="Anti-spam mutes use a role named “Muted” (created if missing). Bot needs Manage Roles and channel perms as needed."
        )
        await ctx.send(embed=help_message)

    # --- Anti-Spam ---
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam(self, ctx):
        """Configure anti-spam settings."""
        settings = await self.config.guild(ctx.guild).all()
        embed = discord.Embed(title="Anti-Spam Settings", color=0xff6b6b)
        embed.add_field(name="Enabled", value="Yes" if settings["antispam_enabled"] else "No", inline=True)
        embed.add_field(name="Message Limit", value=str(settings["antispam_message_limit"]), inline=True)
        embed.add_field(name="Time Window", value=f"{settings['antispam_time_window']}s", inline=True)
        embed.add_field(name="Action", value=settings["antispam_action"], inline=True)
        embed.add_field(name="Mute Duration", value=f"{settings['antispam_mute_duration']}s", inline=True)
        embed.set_footer(text="Use subcommands to configure: enable, disable, limit, window, action, mutetime")
        await ctx.send(embed=embed)

    @antispam.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_enable(self, ctx):
        """Enable anti-spam protection."""
        await self.config.guild(ctx.guild).antispam_enabled.set(True)
        await ctx.send("Anti-spam protection enabled.")

    @antispam.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_disable(self, ctx):
        """Disable anti-spam protection."""
        await self.config.guild(ctx.guild).antispam_enabled.set(False)
        await ctx.send("Anti-spam protection disabled.")

    @antispam.command(name="limit")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_limit(self, ctx, limit: int):
        """Set the message limit before triggering anti-spam (default: 5)."""
        if limit < 2 or limit > 20:
            await ctx.send("Limit must be between 2 and 20.")
            return
        await self.config.guild(ctx.guild).antispam_message_limit.set(limit)
        await ctx.send(f"Anti-spam message limit set to {limit}.")

    @antispam.command(name="window")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_window(self, ctx, seconds: int):
        """Set the time window in seconds (default: 5)."""
        if seconds < 2 or seconds > 30:
            await ctx.send("Window must be between 2 and 30 seconds.")
            return
        await self.config.guild(ctx.guild).antispam_time_window.set(seconds)
        await ctx.send(f"Anti-spam time window set to {seconds} seconds.")

    @antispam.command(name="action")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_action(self, ctx, action: str):
        """Set the action when spam is detected: mute, kick, or warn."""
        action = action.lower()
        if action not in ("mute", "kick", "warn"):
            await ctx.send("Action must be `mute`, `kick`, or `warn`.")
            return
        await self.config.guild(ctx.guild).antispam_action.set(action)
        await ctx.send(f"Anti-spam action set to {action}.")

    @antispam.command(name="mutetime")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_mutetime(self, ctx, seconds: int):
        """Set mute duration in seconds (default: 300 = 5 minutes)."""
        if seconds < 10 or seconds > 86400:
            await ctx.send("Mute duration must be between 10 and 86400 seconds (24 hours).")
            return
        await self.config.guild(ctx.guild).antispam_mute_duration.set(seconds)
        await ctx.send(f"Anti-spam mute duration set to {seconds} seconds.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Award leveling XP and monitor messages for spam."""
        if not message.guild:
            return
        if message.author.bot:
            return
        await self._maybe_award_xp(message)
        if not message.author.guild_permissions.send_messages:
            return
        # Skip if user has manage_messages (moderator)
        if message.author.guild_permissions.manage_messages:
            return

        settings = await self.config.guild(message.guild).all()
        if not settings["antispam_enabled"]:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.utcnow()
        time_window = timedelta(seconds=settings["antispam_time_window"])

        # Clean old messages from cache
        self.message_cache[guild_id][user_id] = [
            ts for ts in self.message_cache[guild_id][user_id]
            if now - ts < time_window
        ]

        # Add current message
        self.message_cache[guild_id][user_id].append(now)

        # Check if over limit
        if len(self.message_cache[guild_id][user_id]) >= settings["antispam_message_limit"]:
            # Clear cache to prevent repeat triggers
            self.message_cache[guild_id][user_id] = []
            await self._handle_spam(message, settings)

    async def _handle_spam(self, message, settings):
        """Handle detected spam based on configured action."""
        member = message.author
        action = settings["antispam_action"]
        reason = "Automatic anti-spam action"

        try:
            if action == "mute":
                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted", reason="Anti-spam mute role")
                    for channel in message.guild.channels:
                        try:
                            await channel.set_permissions(muted_role, send_messages=False, speak=False)
                        except discord.Forbidden:
                            pass
                await member.add_roles(muted_role, reason=reason)
                await message.channel.send(f"{member.mention} has been muted for spamming.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was muted for spamming in {message.channel.mention}.")

                duration = settings["antispam_mute_duration"]
                asyncio.create_task(
                    self._antispam_unmute_later(message.guild, member.id, muted_role, duration)
                )

            elif action == "kick":
                try:
                    await member.send(f"You have been kicked from **{message.guild.name}** for spamming.")
                except Exception:
                    pass
                await member.kick(reason=reason)
                await message.channel.send(f"{member} has been kicked for spamming.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was kicked for spamming in {message.channel.mention}.")

            elif action == "warn":
                try:
                    await member.send(f"⚠️ Warning: You are sending messages too fast in **{message.guild.name}**. Please slow down.")
                except Exception:
                    pass
                await message.channel.send(f"⚠️ {member.mention}, please slow down! You're sending messages too fast.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was warned for spamming in {message.channel.mention}.")

        except discord.Forbidden:
            await self._log_action(message.guild, f"[Anti-Spam] Failed to take action on {member} - missing permissions.")
        except Exception as e:
            await self._log_action(message.guild, f"[Anti-Spam] Error handling spam from {member}: {e}")

    async def _antispam_unmute_later(
        self,
        guild: discord.Guild,
        member_id: int,
        muted_role: discord.Role,
        duration: int,
    ):
        """Schedule outside ``on_message`` so the listener is not blocked for the whole mute duration."""
        await asyncio.sleep(duration)
        try:
            member = guild.get_member(member_id)
            if member is None:
                try:
                    member = await guild.fetch_member(member_id)
                except discord.NotFound:
                    return
            if muted_role in member.roles:
                await member.remove_roles(muted_role, reason="Anti-spam mute expired")
            await self._log_action(
                guild,
                f"[Anti-Spam] {member} was automatically unmuted after {duration}s.",
            )
        except discord.Forbidden:
            await self._log_action(
                guild,
                f"[Anti-Spam] Could not auto-unmute <@{member_id}> — missing permissions.",
            )
        except Exception as e:
            await self._log_action(guild, f"[Anti-Spam] Auto-unmute error for <@{member_id}>: {e}")

    # --- Role Button Verification ---
    @serverassistant.command(name="verifybutton")
    @commands.has_permissions(manage_roles=True)
    async def verifybutton(self, ctx, channel: discord.TextChannel = None, role: discord.Role = None):
        """Send a verification message with a button to assign a role (default: @Verified)."""
        channel = channel or ctx.channel
        if not role:
            role = discord.utils.get(ctx.guild.roles, name="Verified")
            if not role:
                await ctx.send("No role specified and no 'Verified' role found.")
                return
        embed = discord.Embed(
            title="Verification Required",
            description=f"Click the button below to verify and get access to the server!\nYou will be given the {role.mention} role.",
            color=0x43b581
        )
        view = VerifyView(self, role.id)
        await channel.send(embed=embed, view=view)

        ids = await self.config.guild(ctx.guild).verify_button_roles()
        if role.id not in ids:
            ids = list(ids) + [role.id]
            await self.config.guild(ctx.guild).verify_button_roles.set(ids)
        self._register_verify_view(role.id)

        await ctx.send(f"Verification message sent to {channel.mention}.")

    # --- Autorole ---
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
    async def autorole(self, ctx):
        """Auto role assignment settings."""
        role_id = await self.config.guild(ctx.guild).autorole()
        role = ctx.guild.get_role(role_id) if role_id else None
        await ctx.send(f"Current autorole: {role.mention if role else 'None'}")

    @autorole.command(name="set")
    @commands.admin_or_permissions(manage_roles=True)
    async def autorole_set(self, ctx, role: discord.Role):
        """Set a role to auto-assign to new members."""
        await self.config.guild(ctx.guild).autorole.set(role.id)
        await ctx.send(f"Autorole set to: {role.mention}")

    @autorole.command(name="clear")
    @commands.admin_or_permissions(manage_roles=True)
    async def autorole_clear(self, ctx):
        """Clear the autorole setting."""
        await self.config.guild(ctx.guild).autorole.set(None)
        await ctx.send("Autorole has been cleared.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = await self.config.guild(member.guild).autorole()
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto role assignment")
                except discord.Forbidden:
                    pass

    # --- Announce ---
    @serverassistant.command()
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send a plain-text announcement to a channel."""
        await channel.send(message)
        await ctx.send(f"Announcement sent to {channel.mention}")

    @serverassistant.command(name="announceembed")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        channel="Where to post",
        title="Embed title",
        description="Embed body text",
        ping_here="Include @here",
        ping_everyone="Include @everyone (use sparingly)",
        color_hex="Optional color like #5865F2 or 5865F2",
    )
    async def announce_embed(
        self,
        ctx,
        channel: discord.TextChannel,
        title: str,
        description: str,
        ping_here: bool = False,
        ping_everyone: bool = False,
        color_hex: Optional[str] = None,
    ):
        """Post a rich embed announcement; optional @here / @everyone in the same message."""
        color = discord.Color.blurple()
        if color_hex:
            hx = color_hex.strip().lstrip("#")
            if len(hx) == 6 and all(c in "0123456789abcdefABCDEF" for c in hx):
                color = discord.Color(int(hx, 16))
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=f"Announced by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        parts = []
        if ping_here:
            parts.append("@here")
        if ping_everyone:
            parts.append("@everyone")
        content = " ".join(parts) if parts else None
        allow_everyone_mentions = ping_everyone or ping_here
        await channel.send(
            content=content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=allow_everyone_mentions,
                roles=False,
                users=False,
            ),
        )
        await ctx.send(f"Embed announcement sent to {channel.mention}.")

    # --- Slowmode ---
    @serverassistant.hybrid_group(name="slowmode", invoke_without_command=True, fallback="show")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, channel: Optional[discord.TextChannel] = None):
        """View or set channel slowmode (0–21600 seconds)."""
        channel = channel or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Use this in a text channel or pass a text channel.")
            return
        await ctx.send(f"Slowmode in {channel.mention} is **{channel.slowmode_delay}** seconds.")

    @slowmode.command(name="set")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Text channel (defaults to current)", seconds="Delay in seconds; 0 turns slowmode off")
    async def slowmode_set(
        self,
        ctx,
        seconds: commands.Range[int, 0, 21600],
        channel: Optional[discord.TextChannel] = None,
    ):
        """Set slowmode delay for a text channel."""
        channel = channel or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Target must be a text channel.")
            return
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Slowmode for {channel.mention} set to **{seconds}s**.")
        await self._log_action(ctx.guild, f"{ctx.author} set slowmode to {seconds}s in {channel.mention}.")

    # --- Lock / unlock ---
    @serverassistant.command()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Text or forum channel (defaults to here)")
    async def lock(self, ctx, channel: Optional[Union[discord.TextChannel, discord.ForumChannel]] = None):
        """Stop @everyone from sending messages in this text (or forum) channel."""
        channel = channel or ctx.channel
        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            await ctx.send("Lock only applies to text or forum channels.")
            return
        await self._apply_text_lock(channel, ctx.guild, True)
        await ctx.send(f"{channel.mention} is now **locked**.")
        await self._log_action(ctx.guild, f"{ctx.author} locked {channel.mention}.")

    @serverassistant.command()
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="Text or forum channel (defaults to here)")
    async def unlock(self, ctx, channel: Optional[Union[discord.TextChannel, discord.ForumChannel]] = None):
        """Restore default send permissions for @everyone."""
        channel = channel or ctx.channel
        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            await ctx.send("Unlock only applies to text or forum channels.")
            return
        await self._apply_text_lock(channel, ctx.guild, False)
        await ctx.send(f"{channel.mention} is now **unlocked**.")
        await self._log_action(ctx.guild, f"{ctx.author} unlocked {channel.mention}.")

    @serverassistant.command(name="lockcategory")
    @commands.has_permissions(manage_channels=True)
    async def lock_category(self, ctx, category: discord.CategoryChannel):
        """Lock all text channels under a category."""
        n = 0
        for ch in category.channels:
            if isinstance(ch, (discord.TextChannel, discord.ForumChannel)):
                try:
                    await self._apply_text_lock(ch, ctx.guild, True)
                    n += 1
                except discord.Forbidden:
                    pass
        await ctx.send(f"Locked **{n}** channel(s) under **{category.name}**.")
        await self._log_action(ctx.guild, f"{ctx.author} locked category **{category.name}** ({n} channels).")

    @serverassistant.command(name="unlockcategory")
    @commands.has_permissions(manage_channels=True)
    async def unlock_category(self, ctx, category: discord.CategoryChannel):
        """Unlock all text channels under a category."""
        n = 0
        for ch in category.channels:
            if isinstance(ch, (discord.TextChannel, discord.ForumChannel)):
                try:
                    await self._apply_text_lock(ch, ctx.guild, False)
                    n += 1
                except discord.Forbidden:
                    pass
        await ctx.send(f"Unlocked **{n}** channel(s) under **{category.name}**.")
        await self._log_action(ctx.guild, f"{ctx.author} unlocked category **{category.name}** ({n} channels).")

    # --- Poll ---
    @serverassistant.command()
    @app_commands.describe(
        question="The poll question",
        option1="First option (required)",
        option2="Second option (required)",
        option3="Third option",
        option4="Fourth option",
        option5="Fifth option",
        option6="Sixth option",
        option7="Seventh option",
        option8="Eighth option",
        option9="Ninth option",
        option10="Tenth option",
    )
    async def poll(self, ctx, question: str, option1: str, option2: str,
                   option3: str = None, option4: str = None, option5: str = None,
                   option6: str = None, option7: str = None, option8: str = None,
                   option9: str = None, option10: str = None):
        """Create a poll with up to 10 options. Closes automatically after 5 minutes."""
        options = [o for o in [option1, option2, option3, option4, option5,
                                option6, option7, option8, option9, option10] if o]
        view = PollView(question, options)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # --- User Info ---
    @serverassistant.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show info about a user."""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info: {member}", color=member.color)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime('%Y-%m-%d %H:%M') if member.joined_at else "Unknown")
        embed.add_field(name="Created", value=member.created_at.strftime('%Y-%m-%d %H:%M'))
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- Role Info ---
    @serverassistant.command()
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Show info about a role."""
        embed = discord.Embed(title=f"Role Info: {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Position", value=role.position)
        await ctx.send(embed=embed)

    # --- Server Stats ---
    @serverassistant.command()
    async def serverstats(self, ctx):
        """Show server statistics."""
        guild = ctx.guild
        embed = discord.Embed(title=f"Server Stats: {guild.name}", color=0x7289da)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Humans", value=sum(1 for m in guild.members if not m.bot))
        embed.add_field(name="Bots", value=sum(1 for m in guild.members if m.bot))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    # --- Server Owners (Bot Owner Only) ---
    @serverassistant.command(name="owners")
    @commands.is_owner()
    async def server_owners(self, ctx):
        """List all server owners that have the bot. (Bot owner only)"""
        owner_map = {}  # {owner_id: {"user": user_obj, "guilds": [guild_names]}}
        for guild in self.bot.guilds:
            oid = guild.owner_id
            if oid not in owner_map:
                owner_map[oid] = {"user": guild.owner, "guilds": []}
            owner_map[oid]["guilds"].append(guild.name)

        # Sort by server count descending
        sorted_owners = sorted(owner_map.values(), key=lambda x: len(x["guilds"]), reverse=True)

        embeds = []
        per_page = 10
        for page_start in range(0, len(sorted_owners), per_page):
            page_owners = sorted_owners[page_start:page_start + per_page]
            embed = discord.Embed(
                title="Server Owners",
                color=discord.Color.gold(),
            )
            for entry in page_owners:
                user = entry["user"]
                guilds = entry["guilds"]
                name = str(user) if user else f"Unknown User"
                value = f"**Servers ({len(guilds)}):** {', '.join(guilds)}"
                embed.add_field(name=name, value=value, inline=False)

            page_num = page_start // per_page + 1
            total_pages = (len(sorted_owners) + per_page - 1) // per_page
            embed.set_footer(text=f"Page {page_num}/{total_pages} — {len(self.bot.guilds)} total servers")
            embeds.append(embed)

        use_ephemeral = ctx.interaction is not None
        for embed in embeds:
            if use_ephemeral:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)

    # --- Moderation Tools ---

    @serverassistant.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot kick someone with an equal or higher role.")
            return
        try:
            await member.kick(reason=reason or f"Kicked by {ctx.author}")
            await ctx.send(f"{member} has been kicked.")
            await self._log_action(ctx.guild, f"{member} was kicked by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member.")
        except Exception as e:
            await ctx.send(f"Failed to kick: {e}")

    @serverassistant.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Ban a member."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot ban someone with an equal or higher role.")
            return
        try:
            await member.ban(reason=reason or f"Banned by {ctx.author}")
            await ctx.send(f"{member} has been banned.")
            await self._log_action(ctx.guild, f"{member} was banned by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member.")
        except Exception as e:
            await ctx.send(f"Failed to ban: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(
        member="Member to mute",
        reason="Optional: start with a duration like `10m`, `2h`, `1d` then the rest is the reason",
    )
    async def mute(self, ctx, member: discord.Member, *, reason: str = ""):
        """Mute a member. Put a duration first for a timed mute (e.g. ``5m spam``). Uses Discord timeout when possible."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot mute someone with an equal or higher role.")
            return
        duration_sec, rest_reason = _split_mute_reason(reason)
        audit_reason = rest_reason or f"Muted by {ctx.author}"

        try:
            if duration_sec:
                td = timedelta(seconds=duration_sec)
                if td > DISCORD_TIMEOUT_MAX:
                    td = DISCORD_TIMEOUT_MAX
                me = ctx.guild.me
                can_timeout = (
                    me
                    and me.guild_permissions.moderate_members
                    and member.top_role < me.top_role
                    and ctx.guild.owner_id != member.id
                )
                if can_timeout:
                    await member.timeout(td, reason=audit_reason)
                    await ctx.send(f"{member.mention} timed out (**{duration_sec}s**, Discord native).")
                    await self._log_action(
                        ctx.guild,
                        f"{member} timed out by {ctx.author} for {duration_sec}s. Reason: {rest_reason or 'None'}",
                    )
                    return

            muted_role = await self._get_or_create_muted_role(ctx.guild)
            await member.add_roles(muted_role, reason=audit_reason)
            if duration_sec:
                asyncio.create_task(
                    self._delayed_remove_muted_role(ctx.guild, member.id, muted_role, duration_sec)
                )
                await ctx.send(
                    f"{member.mention} muted (**Muted** role) for **{duration_sec}s**."
                )
                await self._log_action(
                    ctx.guild,
                    f"{member} muted by {ctx.author} for {duration_sec}s. Reason: {rest_reason or 'None'}",
                )
            else:
                await ctx.send(f"{member.mention} has been muted (**Muted** role).")
                await self._log_action(
                    ctx.guild,
                    f"{member} muted by {ctx.author}. Reason: {rest_reason or 'None'}",
                )
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this member.")
        except Exception as e:
            await ctx.send(f"Failed to mute: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove Muted role and clear Discord timeout if any."""
        had_timeout = member.communication_disabled_until is not None
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        had_muted_role = muted_role is not None and muted_role in member.roles
        if not had_timeout and not had_muted_role:
            await ctx.send("That member has no active timeout and no **Muted** role.")
            return
        try:
            await member.timeout(None)
        except (discord.Forbidden, discord.HTTPException):
            pass
        if had_muted_role:
            try:
                await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            except discord.Forbidden:
                await ctx.send("I couldn't remove the **Muted** role (check hierarchy).")
                return
        await ctx.send(f"{member.mention} has been unmuted.")
        await self._log_action(ctx.guild, f"{member} was unmuted by {ctx.author}.")

    @serverassistant.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Purge a number of messages (max 100)."""
        if amount < 1 or amount > 100:
            await ctx.send("Amount must be between 1 and 100.")
            return
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
            await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)
            await self._log_action(ctx.guild, f"{ctx.author} purged {len(deleted) - 1} messages in {ctx.channel.mention}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except Exception as e:
            await ctx.send(f"Failed to purge: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """Warn a member (sends DM)."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot warn someone with an equal or higher role.")
            return
        try:
            await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**.\nReason: {reason or 'No reason provided.'}")
            await ctx.send(f"{member} has been warned.")
            await self._log_action(ctx.guild, f"{member} was warned by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send(f"{member} has DMs disabled, but the warning has been logged.")
            await self._log_action(ctx.guild, f"{member} was warned by {ctx.author}. Reason: {reason or 'No reason provided'} (DM failed)")

    async def _log_action(self, guild, message):
        log_channel_id = await self.config.guild(guild).log_channel()
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                try:
                    await channel.send(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {message}")
                except discord.Forbidden:
                    pass

    # --- Logging ---
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
    async def log(self, ctx):
        """Logging settings."""
        log_channel_id = await self.config.guild(ctx.guild).log_channel()
        channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None
        await ctx.send(f"Current log channel: {channel.mention if channel else 'None'}")

    @log.command(name="set")
    @commands.admin_or_permissions(manage_guild=True)
    async def log_set(self, ctx, channel: discord.TextChannel):
        """Set a channel for logging moderation actions."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to: {channel.mention}")

    @log.command(name="clear")
    @commands.admin_or_permissions(manage_guild=True)
    async def log_clear(self, ctx):
        """Clear the log channel setting."""
        await self.config.guild(ctx.guild).log_channel.set(None)
        await ctx.send("Log channel has been cleared.")

    # --- Color Roles ---
    @serverassistant.command(name="createcolorroles")
    @commands.has_permissions(manage_roles=True)
    async def create_color_roles(self, ctx):
        """Create a set of predefined color roles."""
        colors = {}
        for group in COLOR_ROLES.values():
            colors.update(group)

        created_roles = []
        skipped_roles = []

        for color_name, color in colors.items():
            if discord.utils.get(ctx.guild.roles, name=color_name):
                skipped_roles.append(color_name)
            else:
                try:
                    await ctx.guild.create_role(name=color_name, color=color)
                    created_roles.append(color_name)
                except discord.Forbidden:
                    await ctx.send("I don't have permission to create roles.")
                    return

        if created_roles:
            await ctx.send(f"Created roles: {', '.join(created_roles)}")
        if skipped_roles:
            await ctx.send(f"Skipped existing roles: {', '.join(skipped_roles)}")
        if not created_roles and not skipped_roles:
            await ctx.send("No roles to create.")

    # --- Color Picker ---
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
    @commands.has_permissions(manage_roles=True)
    async def colorpicker(self, ctx):
        """Color picker settings."""
        ch_id = await self.config.guild(ctx.guild).colorpicker_channel()
        channel = ctx.guild.get_channel(ch_id) if ch_id else None
        await ctx.send(f"Color picker channel: {channel.mention if channel else 'Not set up'}")

    @colorpicker.command(name="setup")
    @commands.has_permissions(manage_roles=True)
    async def colorpicker_setup(self, ctx, channel: discord.TextChannel = None):
        """Set up the color role picker. Optionally specify a channel, or one will be created."""
        if channel is None:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    send_messages=False, add_reactions=False
                ),
                ctx.guild.me: discord.PermissionOverwrite(
                    send_messages=True, manage_messages=True
                ),
            }
            channel = await ctx.guild.create_text_channel(
                "color-roles", overwrites=overwrites, reason="Color picker setup"
            )

        embed = discord.Embed(
            title="Choose Your Role Color",
            description=(
                "Pick a color from the dropdowns below to set your name color!\n\n"
                "You can only have **one** color role at a time — "
                "choosing a new one will replace your current color."
            ),
            color=discord.Color.from_rgb(255, 255, 255),
        )
        view = ColorPickerView(self)
        msg = await channel.send(embed=embed, view=view)

        await self.config.guild(ctx.guild).colorpicker_channel.set(channel.id)
        await self.config.guild(ctx.guild).colorpicker_message.set(msg.id)

        await ctx.send(f"Color picker set up in {channel.mention}!")

    # --- Leveling ---
    @serverassistant.hybrid_group(name="level", invoke_without_command=True, fallback="show")
    async def level_cmd(self, ctx, member: Optional[discord.Member] = None):
        """Show XP / level, or configure leveling (subcommands)."""
        member = member or ctx.author
        if member.bot:
            await ctx.send("Bots don't have levels here.")
            return
        xp = await self.config.member(member).xp()
        lvl, into, span = _xp_progress(xp)
        low, _ = _xp_band(lvl)
        next_lvl = lvl + 1
        embed = discord.Embed(
            title=f"Level — {member.display_name}",
            color=member.color if member.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(lvl), inline=True)
        embed.add_field(name="Total XP", value=str(xp), inline=True)
        embed.add_field(
            name="Progress to next",
            value=f"{into} / {span} XP (→ level **{next_lvl}**)",
            inline=False,
        )
        embed.set_footer(text=f"XP floor for current level: {low}")
        await ctx.send(embed=embed)

    @level_cmd.command(name="leaderboard")
    async def level_leaderboard(self, ctx):
        """Top 15 members by XP (cached members only)."""
        rows = []
        for m in ctx.guild.members:
            if m.bot:
                continue
            xp_val = await self.config.member(m).xp()
            if xp_val > 0:
                rows.append((xp_val, m))
        rows.sort(key=lambda x: x[0], reverse=True)
        rows = rows[:15]
        if not rows:
            await ctx.send("No XP recorded yet — keep chatting (if leveling is enabled).")
            return
        lines = []
        for i, (xp_val, m) in enumerate(rows, start=1):
            lines.append(f"**{i}.** {m.display_name} — **Lv {_level_from_xp(xp_val)}** ({xp_val} XP)")
        embed = discord.Embed(title="Level leaderboard", description="\n".join(lines), color=discord.Color.gold())
        await ctx.send(embed=embed)

    @level_cmd.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_enable(self, ctx):
        """Turn on XP from normal messages."""
        await self.config.guild(ctx.guild).leveling_enabled.set(True)
        await ctx.send("Leveling **enabled**.")

    @level_cmd.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_disable(self, ctx):
        """Turn off XP gain."""
        await self.config.guild(ctx.guild).leveling_enabled.set(False)
        await ctx.send("Leveling **disabled**.")

    @level_cmd.command(name="xprange")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_xprange(self, ctx, minimum: int, maximum: int):
        """Random XP per eligible message (min–max, inclusive)."""
        lo, hi = sorted((max(1, minimum), max(1, maximum)))
        await self.config.guild(ctx.guild).leveling_xp_min.set(lo)
        await self.config.guild(ctx.guild).leveling_xp_max.set(hi)
        await ctx.send(f"XP per message set to **{lo}–{hi}**.")

    @level_cmd.command(name="cooldown")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_cooldown_cmd(self, ctx, seconds: commands.Range[int, 5, 3600]):
        """Minimum seconds between XP gains per user."""
        await self.config.guild(ctx.guild).leveling_cooldown.set(seconds)
        await ctx.send(f"Leveling cooldown set to **{seconds}s**.")

    @level_cmd.command(name="ignorechannel")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_ignore_channel(self, ctx, channel: discord.TextChannel):
        """No XP in this channel."""
        ids = list(await self.config.guild(ctx.guild).leveling_ignored_channels())
        if channel.id not in ids:
            ids.append(channel.id)
            await self.config.guild(ctx.guild).leveling_ignored_channels.set(ids)
        await ctx.send(f"{channel.mention} ignored for XP.")

    @level_cmd.command(name="unignorechannel")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_unignore_channel(self, ctx, channel: discord.TextChannel):
        """Allow XP again in this channel."""
        ids = [i for i in await self.config.guild(ctx.guild).leveling_ignored_channels() if i != channel.id]
        await self.config.guild(ctx.guild).leveling_ignored_channels.set(ids)
        await ctx.send(f"{channel.mention} no longer ignored for XP.")

    @level_cmd.command(name="ignorerole")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_ignore_role(self, ctx, role: discord.Role):
        """Members with this role earn no XP."""
        ids = list(await self.config.guild(ctx.guild).leveling_ignored_roles())
        if role.id not in ids:
            ids.append(role.id)
            await self.config.guild(ctx.guild).leveling_ignored_roles.set(ids)
        await ctx.send(f"Role {role.mention} ignored for XP.")

    @level_cmd.command(name="unignorerole")
    @commands.admin_or_permissions(manage_guild=True)
    async def level_unignore_role(self, ctx, role: discord.Role):
        ids = [i for i in await self.config.guild(ctx.guild).leveling_ignored_roles() if i != role.id]
        await self.config.guild(ctx.guild).leveling_ignored_roles.set(ids)
        await ctx.send(f"Role {role.mention} no longer ignored for XP.")

    # --- Starboard ---
    @serverassistant.hybrid_group(name="starboard", invoke_without_command=True, fallback="show")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_cmd(self, ctx):
        """Starboard: highlight messages that reach a reaction threshold."""
        s = await self.config.guild(ctx.guild).all()
        ch = ctx.guild.get_channel(s["starboard_channel"]) if s["starboard_channel"] else None
        embed = discord.Embed(title="Starboard settings", color=discord.Color.gold())
        embed.add_field(name="Channel", value=ch.mention if ch else "Not set", inline=True)
        embed.add_field(name="Minimum", value=str(s["starboard_min"]), inline=True)
        embed.add_field(name="Emoji", value=s["starboard_emoji"], inline=True)
        embed.add_field(
            name="Ignore self-star",
            value="Yes" if s["starboard_ignore_self"] else "No",
            inline=True,
        )
        embed.set_footer(text="Use: set, disable, minimum, emoji, selfstar")
        await ctx.send(embed=embed)

    @starboard_cmd.command(name="set")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_set(self, ctx, channel: discord.TextChannel):
        """Posts will be copied/reposted here when they reach the minimum."""
        await self.config.guild(ctx.guild).starboard_channel.set(channel.id)
        await ctx.send(f"Starboard channel set to {channel.mention}.")

    @starboard_cmd.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_disable(self, ctx):
        await self.config.guild(ctx.guild).starboard_channel.set(None)
        await ctx.send("Starboard **disabled** (channel cleared).")

    @starboard_cmd.command(name="minimum")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_minimum(self, ctx, count: commands.Range[int, 1, 50]):
        await self.config.guild(ctx.guild).starboard_min.set(count)
        await ctx.send(f"Starboard minimum reactions set to **{count}**.")

    @starboard_cmd.command(name="emoji")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_emoji_cmd(self, ctx, emoji: str):
        """Unicode emoji or custom format ``name:id`` / ``<:name:id>``."""
        emoji = emoji.strip()
        await self.config.guild(ctx.guild).starboard_emoji.set(emoji)
        await ctx.send(f"Starboard emoji set to {emoji}")

    @starboard_cmd.command(name="selfstar")
    @commands.admin_or_permissions(manage_guild=True)
    async def starboard_selfstar(self, ctx, enabled: bool):
        """Whether the author's own reaction counts toward the minimum."""
        await self.config.guild(ctx.guild).starboard_ignore_self.set(not enabled)
        await ctx.send(f"Self-stars **{'count' if enabled else 'do not count'}** toward the minimum.")

    # --- Reaction roles ---
    @serverassistant.hybrid_group(name="reactionrole", invoke_without_command=True, fallback="list")
    @commands.admin_or_permissions(manage_roles=True)
    async def reactionrole(self, ctx):
        """Map message reactions to roles (classic reaction roles)."""
        maps = await self.config.guild(ctx.guild).reaction_roles()
        if not maps:
            await ctx.send("No reaction-role mappings. Use `add`.")
            return
        lines = []
        for mid, bucket in list(maps.items())[:15]:
            bits = ", ".join(f"`{k}` → {ctx.guild.get_role(rid) or rid}" for k, rid in bucket.items())
            lines.append(f"• message `{mid}`\n  {bits}")
        if len(maps) > 15:
            lines.append(f"*…and {len(maps) - 15} more*")
        await ctx.send(embed=discord.Embed(title="Reaction roles", description="\n".join(lines)[:4000] or "—"))

    @reactionrole.command(name="add")
    @commands.admin_or_permissions(manage_roles=True)
    async def reactionrole_add(
        self,
        ctx,
        message: discord.Message,
        emoji: str,
        role: discord.Role,
    ):
        """Add a mapping. The bot will add the same reaction to the message."""
        try:
            pe = discord.PartialEmoji.from_str(emoji.strip())
        except Exception:
            pe = discord.PartialEmoji(name=emoji.strip())
        key = _emoji_key(pe)
        maps = dict(await self.config.guild(ctx.guild).reaction_roles())
        mid = str(message.id)
        bucket = dict(maps.get(mid, {}))
        bucket[key] = role.id
        maps[mid] = bucket
        await self.config.guild(ctx.guild).reaction_roles.set(maps)
        try:
            await message.add_reaction(pe)
        except discord.HTTPException:
            pass
        await ctx.send(f"Linked {emoji} on [that message]({message.jump_url}) → {role.mention}.")

    @reactionrole.command(name="remove")
    @commands.admin_or_permissions(manage_roles=True)
    async def reactionrole_remove(self, ctx, message: discord.Message, emoji: str):
        try:
            pe = discord.PartialEmoji.from_str(emoji.strip())
        except Exception:
            pe = discord.PartialEmoji(name=emoji.strip())
        key = _emoji_key(pe)
        maps = dict(await self.config.guild(ctx.guild).reaction_roles())
        mid = str(message.id)
        bucket = dict(maps.get(mid, {}))
        bucket.pop(key, None)
        if bucket:
            maps[mid] = bucket
        else:
            maps.pop(mid, None)
        await self.config.guild(ctx.guild).reaction_roles.set(maps)
        await ctx.send("Mapping removed for that emoji on that message.")

    @reactionrole.command(name="clear")
    @commands.admin_or_permissions(manage_roles=True)
    async def reactionrole_clear(self, ctx, message: discord.Message):
        maps = dict(await self.config.guild(ctx.guild).reaction_roles())
        maps.pop(str(message.id), None)
        await self.config.guild(ctx.guild).reaction_roles.set(maps)
        await ctx.send("All reaction roles cleared for that message.")

    # --- Role menu (select menu) ---
    @serverassistant.hybrid_group(name="rolemenu", invoke_without_command=True, fallback="help")
    @commands.admin_or_permissions(manage_roles=True)
    async def rolemenu(self, ctx):
        await ctx.send(
            f"**Role menu** — post a multi-select in a channel:\n"
            f"`{ctx.clean_prefix}serverassistant rolemenu send #channel \"Title\" @Role1 @Role2 ...` (max 25)\n"
            f"`{ctx.clean_prefix}serverassistant rolemenu remove <message_id>`"
        )

    @rolemenu.command(name="send", with_app_command=False)
    @commands.admin_or_permissions(manage_roles=True)
    async def rolemenu_send(self, ctx, channel: discord.TextChannel, title: str, roles: commands.Greedy[discord.Role]):
        """Post a persistent dropdown; members can toggle any of the listed roles."""
        if not roles or len(roles) > 25:
            await ctx.send("Provide between **1** and **25** roles after the title.")
            return
        me = ctx.guild.me
        for r in roles:
            if r >= me.top_role and ctx.author != ctx.guild.owner:
                await ctx.send(f"I can't assign {r.name} — it's above my top role.")
                return
        role_ids = [r.id for r in roles]
        embed = discord.Embed(
            title=title,
            description="Use the menu below to add or remove roles.",
            color=discord.Color.blurple(),
        )
        msg = await channel.send(embed=embed)
        view = RoleMenuView(self, ctx.guild, msg.id, role_ids)
        await msg.edit(view=view)
        menus = dict(await self.config.guild(ctx.guild).role_menus())
        menus[str(msg.id)] = {"channel_id": channel.id, "roles": role_ids}
        await self.config.guild(ctx.guild).role_menus.set(menus)
        self._register_role_menu_view(ctx.guild, msg.id, role_ids, view=view)
        await ctx.send(f"Role menu posted in {channel.mention}.")

    @rolemenu.command(name="remove")
    @commands.admin_or_permissions(manage_roles=True)
    async def rolemenu_remove(self, ctx, message_id: int):
        """Remove a role menu from config and try to delete its message."""
        menus = dict(await self.config.guild(ctx.guild).role_menus())
        key = str(message_id)
        data = menus.pop(key, None)
        await self.config.guild(ctx.guild).role_menus.set(menus)
        self._role_menu_message_ids.discard(message_id)
        if data:
            ch = ctx.guild.get_channel(data.get("channel_id"))
            if ch:
                try:
                    m = await ch.fetch_message(message_id)
                    await m.delete()
                except Exception:
                    pass
        await ctx.send("Role menu removed from config" + (" and message deleted." if data else "."))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self._handle_starboard_raw(payload, added=True)
        await self._handle_reaction_role_raw(payload, added=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self._handle_starboard_raw(payload, added=False)
        await self._handle_reaction_role_raw(payload, added=False)

    async def _starboard_emoji_matches(self, guild: discord.Guild, payload: discord.RawReactionActionEvent) -> bool:
        want = await self.config.guild(guild).starboard_emoji()
        got = _emoji_key(payload.emoji)
        try:
            pe = discord.PartialEmoji.from_str(want.strip())
            want_key = _emoji_key(pe)
        except Exception:
            want_key = want.strip()
        return got == want_key

    async def _handle_starboard_raw(self, payload: discord.RawReactionActionEvent, *, added: bool) -> None:
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        settings = await self.config.guild(guild).all()
        sb_id = settings["starboard_channel"]
        if not sb_id:
            return
        if payload.channel_id == sb_id:
            return
        if not await self._starboard_emoji_matches(guild, payload):
            return
        channel = guild.get_channel(payload.channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            return
        r_obj = None
        for r in message.reactions:
            if _emoji_key(r.emoji) == _emoji_key(payload.emoji):
                r_obj = r
                break
        react_count = 0
        if r_obj:
            if settings["starboard_ignore_self"]:
                async for u in r_obj.users(limit=None):
                    if u.id != message.author.id:
                        react_count += 1
            else:
                react_count = r_obj.count
        sb_channel = guild.get_channel(sb_id)
        if not sb_channel or not isinstance(sb_channel, discord.TextChannel):
            return
        posts = dict(settings["starboard_posts"] or {})
        mid_key = str(message.id)
        min_stars = max(1, int(settings["starboard_min"]))

        if react_count < min_stars:
            existing_sb_id = posts.get(mid_key)
            if existing_sb_id:
                try:
                    sm = await sb_channel.fetch_message(existing_sb_id)
                    await sm.delete()
                except discord.HTTPException:
                    pass
                posts.pop(mid_key, None)
                await self.config.guild(guild).starboard_posts.set(posts)
            return

        content = message.content[:250] + ("…" if len(message.content) > 250 else "") if message.content else "*No text*"
        embed = discord.Embed(
            description=content,
            color=discord.Color.gold(),
            timestamp=message.created_at,
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Source", value=f"[Jump to message]({message.jump_url})", inline=False)
        if message.attachments and message.attachments[0].content_type and str(message.attachments[0].content_type).startswith("image/"):
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(text=f"{react_count} {settings['starboard_emoji']} · #{channel.name}")

        existing_sb_id = posts.get(mid_key)
        if existing_sb_id:
            try:
                sm = await sb_channel.fetch_message(existing_sb_id)
                await sm.edit(embed=embed)
            except discord.HTTPException:
                try:
                    sm = await sb_channel.send(embed=embed)
                    posts[mid_key] = sm.id
                    await self.config.guild(guild).starboard_posts.set(posts)
                except discord.HTTPException:
                    pass
        else:
            try:
                sm = await sb_channel.send(embed=embed)
                posts[mid_key] = sm.id
                await self.config.guild(guild).starboard_posts.set(posts)
            except discord.HTTPException:
                pass

    async def _handle_reaction_role_raw(self, payload: discord.RawReactionActionEvent, *, added: bool) -> None:
        if not payload.guild_id or not payload.user_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        maps = await self.config.guild(guild).reaction_roles()
        bucket = maps.get(str(payload.message_id))
        if not bucket:
            return
        key = _emoji_key(payload.emoji)
        role_id = bucket.get(key)
        if not role_id:
            return
        role = guild.get_role(role_id)
        if not role:
            return
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        me = guild.me
        if not me or not me.guild_permissions.manage_roles or role >= me.top_role:
            return
        try:
            if added:
                if role not in member.roles:
                    await member.add_roles(role, reason="Reaction role")
            else:
                if role in member.roles:
                    await member.remove_roles(role, reason="Reaction role removed")
        except discord.Forbidden:
            pass

    # --- Channel Map ---
    @serverassistant.command(name="channelmap")
    async def channel_map(self, ctx):
        """Generate a mind map of the server's channels."""
        channel_list = list(ctx.guild.channels)
        channel_list.sort(key=lambda x: (x.position, str(x.type)))

        tree_string = "Server Channel Structure:\n"
        for channel in channel_list:
            if isinstance(channel, discord.CategoryChannel):
                tree_string += f"📁 {channel.name}\n"
                for sub_channel in sorted(channel.channels, key=lambda x: x.position):
                    if isinstance(sub_channel, discord.TextChannel):
                        tree_string += f"  💬 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.VoiceChannel):
                        tree_string += f"  🔊 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.StageChannel):
                        tree_string += f"  🎭 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.ForumChannel):
                        tree_string += f"  📋 {sub_channel.name}\n"
                    else:
                        tree_string += f"  ❓ {sub_channel.name}\n"
            elif channel.category is None:
                if isinstance(channel, discord.TextChannel):
                    tree_string += f"💬 {channel.name}\n"
                elif isinstance(channel, discord.VoiceChannel):
                    tree_string += f"🔊 {channel.name}\n"

        if len(tree_string) > 1990:
            chunks = [tree_string[i:i+1980] for i in range(0, len(tree_string), 1980)]
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")
        else:
            await ctx.send(f"```{tree_string}```")


class RoleMenuSelect(discord.ui.Select):
    """Persistent multi-select; chosen roles are toggled against the member."""

    def __init__(self, cog: "ServerAssistant", guild: discord.Guild, message_id: int, role_ids: list):
        self.cog = cog
        self.message_id = message_id
        opts = []
        for rid in role_ids[:25]:
            role = guild.get_role(rid)
            opts.append(
                discord.SelectOption(
                    label=(role.name if role else f"Deleted ({rid})")[:100],
                    value=str(rid),
                )
            )
        mx = len(opts)
        super().__init__(
            placeholder="Add/remove roles…",
            min_values=0,
            max_values=mx,
            options=opts,
            custom_id=f"serverassistant_rm_{message_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Use this in the server.", ephemeral=True)
            return
        mid = str(interaction.message.id)
        menus = await self.cog.config.guild(guild).role_menus()
        data = menus.get(mid)
        if not data:
            await interaction.response.send_message("This menu is no longer active.", ephemeral=True)
            return
        configured = set(data.get("roles") or [])
        selected = {int(x) for x in self.values}
        have = {r.id for r in member.roles} & configured
        to_add = selected - have
        to_remove = have - selected
        me = guild.me
        if not me or not me.guild_permissions.manage_roles:
            await interaction.response.send_message("I can't manage roles here.", ephemeral=True)
            return
        roles_add = [guild.get_role(r) for r in to_add]
        roles_rem = [guild.get_role(r) for r in to_remove]
        roles_add = [x for x in roles_add if x and x < me.top_role]
        roles_rem = [x for x in roles_rem if x and x < me.top_role]
        try:
            if roles_add:
                await member.add_roles(*roles_add, reason="Role menu")
            if roles_rem:
                await member.remove_roles(*roles_rem, reason="Role menu")
            await interaction.response.send_message("Your roles were updated.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't change those roles (check hierarchy).", ephemeral=True)


class RoleMenuView(discord.ui.View):
    def __init__(self, cog: "ServerAssistant", guild: discord.Guild, message_id: int, role_ids: list):
        super().__init__(timeout=None)
        self.cog = cog
        self.message_id = message_id
        self.add_item(RoleMenuSelect(cog, guild, message_id, role_ids))


class VerifyView(discord.ui.View):
    """Persistent verification button; ``custom_id`` includes the role id so restarts keep working."""

    def __init__(self, cog, role_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.role_id = role_id
        self.add_item(VerifyRoleButton(cog, role_id))


class VerifyRoleButton(discord.ui.Button):
    def __init__(self, cog: "ServerAssistant", role_id: int):
        super().__init__(
            label="Verify",
            style=discord.ButtonStyle.success,
            custom_id=f"serverassistant_verify_{role_id}",
        )
        self.cog = cog
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role = member.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("Verification role not found. Please contact an admin.", ephemeral=True)
            return
        if role in member.roles:
            await interaction.response.send_message("You are already verified!", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason="Verified via button")
            await interaction.response.send_message(f"You have been verified and given the {role.mention} role!", ephemeral=True)
            try:
                await member.send(f"You have been verified in **{member.guild.name}**! Welcome!")
            except discord.Forbidden:
                pass
            log_channel_id = await self.cog.config.guild(member.guild).log_channel()
            if log_channel_id:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    try:
                        await log_channel.send(
                            f"[Verification] {member.mention} ({member.id}) verified at "
                            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}."
                        )
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to assign the role. Please contact an admin.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


class ColorRoleSelect(discord.ui.Select):
    """A single dropdown for a color group."""

    def __init__(self, cog, group_name, colors):
        options = [
            discord.SelectOption(label=name, value=name)
            for name in colors
        ]
        super().__init__(
            placeholder=f"{group_name} Colors",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"serverassistant_color_{group_name.lower()}",
        )
        self.cog = cog
        self.all_color_names = []
        for group in COLOR_ROLES.values():
            self.all_color_names.extend(group.keys())

    async def callback(self, interaction: discord.Interaction):
        color_name = self.values[0]
        guild = interaction.guild
        member = interaction.user

        # Find the role
        role = discord.utils.get(guild.roles, name=color_name)
        if not role:
            await interaction.response.send_message(
                f"The **{color_name}** role doesn't exist. An admin needs to run `/serverassistant createcolorroles` first.",
                ephemeral=True,
            )
            return

        # Remove existing color roles
        existing_color_roles = [
            r for r in member.roles if r.name in self.all_color_names
        ]
        if existing_color_roles:
            await member.remove_roles(*existing_color_roles, reason="Color role change")

        # Assign new color role
        await member.add_roles(role, reason="Color role selection")
        await interaction.response.send_message(
            f"You've been given the **{color_name}** color role!",
            ephemeral=True,
        )


class ColorPickerView(discord.ui.View):
    """Persistent color picker with grouped dropdowns."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        for group_name, colors in COLOR_ROLES.items():
            self.add_item(ColorRoleSelect(cog, group_name, colors))


class PollButton(discord.ui.Button):
    def __init__(self, label, emoji, option_index):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=emoji,
        )
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        old_vote = view.votes.get(interaction.user.id)
        view.votes[interaction.user.id] = self.option_index

        if old_vote == self.option_index:
            await interaction.response.send_message("You already voted for this!", ephemeral=True)
        elif old_vote is not None:
            await interaction.response.send_message(
                f"Changed your vote to: **{view.options[self.option_index]}**", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"You voted for: **{view.options[self.option_index]}**", ephemeral=True
            )

        # Update embed with new counts
        await interaction.message.edit(embed=view.build_embed())


class PollView(discord.ui.View):
    EMOJIS = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3", "6\u20e3", "7\u20e3", "8\u20e3", "9\u20e3", "\U0001f51f"]

    def __init__(self, question, options):
        super().__init__(timeout=300)  # 5 minutes
        self.question = question
        self.options = options
        self.votes = {}  # {user_id: option_index}
        self.message = None

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, emoji=self.EMOJIS[i], option_index=i))

    def build_embed(self, closed=False):
        counts = {}
        for idx in range(len(self.options)):
            counts[idx] = sum(1 for v in self.votes.values() if v == idx)
        total = sum(counts.values())

        desc_lines = []
        for i, opt in enumerate(self.options):
            count = counts[i]
            pct = f" ({count / total * 100:.0f}%)" if total > 0 else ""
            bar = ""
            if closed and total > 0:
                filled = round(count / total * 10)
                full_block = "\u2588"
                light_block = "\u2591"
                bar = f" {full_block * filled}{light_block * (10 - filled)}"
            desc_lines.append(f"{self.EMOJIS[i]} **{opt}** \u2014 {count} vote{'s' if count != 1 else ''}{pct}{bar}")

        if closed:
            max_votes = max(counts.values())
            if total == 0:
                desc_lines.append("\n**No votes were cast.**")
            else:
                winners = [self.options[i] for i, c in counts.items() if c == max_votes]
                if len(winners) == 1:
                    desc_lines.append(f"\n**Winner: {winners[0]}!**")
                else:
                    desc_lines.append(f"\n**Tie: {', '.join(winners)}!**")

        embed = discord.Embed(
            title=f"{'[CLOSED] ' if closed else ''}\U0001f4ca {self.question}",
            description="\n".join(desc_lines),
            color=discord.Color.red() if closed else discord.Color.blue(),
        )
        if not closed:
            embed.set_footer(text="Poll closes in 5 minutes")
        else:
            embed.set_footer(text=f"Final results \u2014 {total} total vote{'s' if total != 1 else ''}")
        return embed

    async def update_embed(self, message):
        await message.edit(embed=self.build_embed())

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        embed = self.build_embed(closed=True)
        if self.message:
            await self.message.edit(embed=embed, view=self)
