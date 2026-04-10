#
# Cooldown buddy — easy BRB/lurk timer, bean proverbs on pings, return when "back" or time's up.
#

from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime, time as dt_time, timedelta, timezone
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import Embed, app_commands
from redbot.core import Config, commands

log = logging.getLogger("red.cooldownbuddy")

_DISMISSIVE: Tuple[str, ...] = (
    "The bean whispers: they’re **steeping**. Let the mug rest.",
    "This grind isn’t ready yet. **Wait for the bloom.**",
    "The portafilter is locked. **Try again after the shot.**",
    "They’re on a **silent extraction**. Don’t tap the glass.",
    "The cosmic café says **not now**—the milk is still texturing.",
    "That user is **off-menu** until further notice.",
    "Beans need rest too. **No pings, only patience.**",
    "The oracle reads the grounds: **away.** Shoo, kindly.",
    "They’re chasing **steam**, not notifications. Back off, legend.",
    "The drip hasn’t finished. **Don’t rush art.**",
    "Currently **decanting** attention elsewhere. Try later.",
    "The French press plunger is **down**. Translation: busy.",
    "Even cold brew takes **hours**. You can wait a few minutes.",
    "The scale says **0.00 drama** until they return.",
    "They’re in **cupping mode**: sniffing life, not Discord.",
    "Barista’s orders: **no poke** while the timer runs.",
    "That mention bounced off a **preheated** “not here” shield.",
    "The bean council votes **latte**—as in, later.",
    "They’re **pulling shots** in real life. Imaginary ones don’t count.",
    "Your ping evaporated like **crema** in the wind.",
    "Still **blooming**. Come back when the crust breaks.",
    "The tamper says **even pressure**—on you, not them.",
    "They’re **offline-roasted** right now. Try after cooldown.",
    "Notification machine **broken**. Blame the grinder (politely).",
    "The café is **closed** for this user. Read the chalkboard.",
)

_RETURN: Tuple[str, ...] = (
    "The bean acknowledges your return. **Welcome back.**",
    "Bloom complete. **You’re poured in.**",
    "Timer dinged—**you’re officially hot again.**",
    "The oracle stirs: **back on the menu.**",
    "Steam cleared. **Your mug is yours again.**",
    "Extraction ended; **presence restored.**",
    "The grind resumes—**good to see you.**",
    "French press **unlocked**. Hi again.",
    "Cold brew patience **paid off**. Welcome.",
    "Scale recalibrated: **you’re here.**",
    "Crema’s back on top—**that’s you.**",
    "The barista nods once. **Return accepted.**",
    "Cup empty of absence; **filled with you.**",
    "Shot pulled; **you’re live.**",
    "Milk integrated—**you’re frothy and present.**",
    "Chalkboard updated: **OPEN (you).**",
    "Beans cheer quietly. **Welcome back.**",
    "The drip tray of life is **dry**; you’re back.",
    "Portafilter **seated**. Hi.",
    "Timer forgiven. **Hello again.**",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_clock(timepart: str, guild_tz_name: str) -> Tuple[Optional[datetime], Optional[str]]:
    """Return (until_utc aware) or (None, error)."""
    name = (guild_tz_name or "UTC").strip()
    try:
        tz = ZoneInfo(name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    now_local = datetime.now(tz)
    s = timepart.strip().upper()

    m12 = re.fullmatch(r"(\d{1,2}):(\d{2})\s*(AM|PM)", s)
    m24 = re.fullmatch(r"(\d{1,2}):(\d{2})", s)
    h, mi = None, None
    if m12:
        hh, mm, ap = int(m12.group(1)), int(m12.group(2)), m12.group(3)
        if not (1 <= hh <= 12 and 0 <= mm <= 59):
            return None, "That 12-hour time doesn’t look valid."
        if ap == "PM":
            h = 12 if hh == 12 else hh + 12
        else:
            h = 0 if hh == 12 else hh
        mi = mm
    elif m24:
        hh, mm = int(m24.group(1)), int(m24.group(2))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None, "That 24-hour time doesn’t look valid."
        h, mi = hh, mm
    else:
        return None, "Use `at 3:30pm` or `at 15:30` (guild timezone via `[p]brbzone`)."

    dt_local = datetime.combine(now_local.date(), dt_time(h, mi), tzinfo=tz)
    if dt_local <= now_local:
        dt_local += timedelta(days=1)
    return dt_local.astimezone(timezone.utc), None


def parse_brb_when(raw: str, guild_tz_name: str) -> Tuple[str, Optional[datetime], Optional[str]]:
    """
    Returns (kind, until_utc, err).

    kind: "clear" | "set" | "bad"
    until_utc set only when kind=="set"
    """
    s = raw.strip().lower()
    if not s:
        return "bad", None, None

    clears = {"back", "clear", "here", "returned", "im back", "i'm back", "imback"}
    if s in clears:
        return "clear", None, None

    m_at = re.match(r"^(?:at|until)\s+(.+)$", raw.strip(), re.I)
    if m_at:
        timepart = m_at.group(1).strip()
        until, err = _parse_clock(timepart, guild_tz_name)
        if err:
            return "bad", None, err
        return "set", until, None

    compact = re.sub(r"\s+", "", s)
    m = re.fullmatch(r"(\d+)h(?:(\d+)m?)?", compact)
    if m:
        hours = int(m.group(1))
        mins = int(m.group(2) or 0)
        if mins > 59:
            return "bad", None, "Minutes after `h` must be **0–59**."
        delta = timedelta(hours=hours, minutes=mins)
        if delta.total_seconds() < 60:
            return "bad", None, "Use at least **1 minute** (e.g. `1m` or `1h`)."
        if delta.total_seconds() > 72 * 3600:
            return "bad", None, "Max away duration is **72 hours**."
        return "set", _utc_now() + delta, None

    m = re.fullmatch(r"(\d+)m", compact)
    if m:
        mins = int(m.group(1))
        if mins < 1 or mins > 4320:  # 72h
            return "bad", None, "Use **1–4320** minutes (max 72 hours)."
        return "set", _utc_now() + timedelta(minutes=mins), None

    m = re.fullmatch(r"\d+", s)
    if m:
        mins = int(s)
        if mins < 1 or mins > 4320:
            return "bad", None, "Plain number = **minutes**. Use **1–4320** (72h max)."
        return "set", _utc_now() + timedelta(minutes=mins), None

    return "bad", None, None


class CooldownBuddy(commands.Cog):
    """BRB / lurk timer with ping deflection and bean proverbs on return."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xBEEBEE01, force_registration=True)
        self.config.register_guild(timezone="UTC")
        self.config.register_member(brb_until=None, brb_channel_id=None)
        self._tasks: Dict[Tuple[int, int], asyncio.Task] = {}
        self._ping_cd: Dict[Tuple[int, int, int], float] = {}

    def cog_unload(self):
        for t in list(self._tasks.values()):
            if t and not t.done():
                t.cancel()

    async def red_delete_data_for_user(self, **kwargs):
        uid = kwargs.get("user_id")
        if uid is None:
            return
        for g in self.bot.guilds:
            await self.config.member_from_ids(g.id, uid).clear()
        for key in list(self._tasks.keys()):
            if key[1] == uid:
                t = self._tasks.pop(key, None)
                if t and not t.done():
                    t.cancel()

    def _cancel_timer(self, guild_id: int, user_id: int) -> None:
        t = self._tasks.pop((guild_id, user_id), None)
        if t is not None and not t.done() and t is not asyncio.current_task():
            t.cancel()

    async def _finish_brb(
        self,
        guild: discord.Guild,
        user_id: int,
        channel_id: int,
        *,
        timed_out: bool,
    ) -> None:
        await self.config.member_from_ids(guild.id, user_id).clear()
        self._cancel_timer(guild.id, user_id)
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return
        member = guild.get_member(user_id)
        mention = member.mention if member else f"<@{user_id}>"
        proverb = random.choice(_RETURN)
        try:
            if timed_out:
                await channel.send(f"{mention} {proverb} *(time’s up)*")
            else:
                await channel.send(f"{mention} {proverb}")
        except discord.HTTPException:
            log.warning("Could not send BRB return message in channel %s", channel_id)

    def _schedule_timer(self, guild_id: int, user_id: int, delay: float, channel_id: int) -> None:
        self._cancel_timer(guild_id, user_id)

        async def _wait():
            try:
                await asyncio.sleep(max(0.0, delay))
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                conf = self.config.member_from_ids(guild_id, user_id)
                until = await conf.brb_until()
                if until is None:
                    return
                if _utc_now().timestamp() + 0.25 < float(until):
                    return
                ch_stored = await conf.brb_channel_id()
                if ch_stored:
                    await self._finish_brb(guild, user_id, int(ch_stored), timed_out=True)
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception("BRB timer failed for guild=%s user=%s", guild_id, user_id)

        self._tasks[(guild_id, user_id)] = asyncio.create_task(_wait())

    @commands.hybrid_command(name="brb", aliases=["beanbrb", "lurk"])
    @commands.guild_only()
    @app_commands.describe(
        when=(
            "Examples: `10` (minutes), `20m`, `1h`, `1h30m`, `at 3:30pm`, `until 15:30`, or `back` to return"
        )
    )
    async def brb_cmd(self, ctx: commands.Context, *, when: Optional[str] = None):
        """
        Set a quick away timer, or say you're back.

        **Minutes:** `10` or `10m` · **Hours:** `1h`, `1h30m` · **Clock:** `at 3:30pm` / `until 15:30` (guild TZ)
        · **Clear:** `back`, `clear`, `here`
        """
        if when is None or not str(when).strip():
            embed = Embed(
                title="☕ Cooldown buddy (BRB)",
                description=(
                    "Set an away timer; if someone **@mentions** you before you’re back, "
                    "I’ll deflect with a **bean proverb**. When you return, say **`back`** here—or wait for the timer."
                ),
                color=0x5D4037,
            )
            embed.add_field(
                name="Easy examples",
                value=(
                    "`/brb 15` — 15 minutes\n"
                    "`/brb 90m` — 90 minutes\n"
                    "`/brb 1h` — one hour\n"
                    "`/brb 1h30m` — one hour thirty\n"
                    "`/brb at 3:45pm` — until that time **today or tomorrow** (guild timezone)\n"
                    "`/brb back` — I’m here again"
                ),
                inline=False,
            )
            tz = await self.config.guild(ctx.guild).timezone()
            embed.set_footer(text=f"Guild timezone for `at`/`until`: {tz} · Admins: /brbzone")
            await ctx.send(embed=embed)
            return

        tz_name = await self.config.guild(ctx.guild).timezone()
        kind, until_utc, err = parse_brb_when(when, tz_name)

        if kind == "bad":
            await ctx.send(
                err
                or "Couldn’t parse that. Try `15`, `15m`, `1h`, `at 3:30pm`, or `back`."
            )
            return

        if kind == "clear":
            conf = self.config.member(ctx.author)
            active = await conf.brb_until()
            if active is None:
                await ctx.send("You’re not on a BRB timer here. You’re **present**—the beans already knew.")
                return
            ch_id = await conf.brb_channel_id()
            await self._finish_brb(ctx.guild, ctx.author.id, int(ch_id or ctx.channel.id), timed_out=False)
            return

        # set
        assert until_utc is not None
        if until_utc <= _utc_now():
            await ctx.send("That time is already in the past. Try a longer duration or a later clock time.")
            return
        max_until = _utc_now() + timedelta(hours=72)
        if until_utc > max_until:
            await ctx.send("Max away length is **72 hours**. The beans refuse longer shifts.")

        self._cancel_timer(ctx.guild.id, ctx.author.id)
        ts = until_utc.timestamp()
        await self.config.member(ctx.author).brb_until.set(ts)
        await self.config.member(ctx.author).brb_channel_id.set(ctx.channel.id)

        delay = ts - _utc_now().timestamp()
        self._schedule_timer(ctx.guild.id, ctx.author.id, delay, ctx.channel.id)

        rel = discord.utils.format_dt(until_utc, "R")
        abs_s = discord.utils.format_dt(until_utc, "f")
        embed = Embed(
            title="☕ BRB locked in",
            description=f"{ctx.author.mention} is away until **{abs_s}** ({rel}).",
            color=0x6D4C41,
        )
        embed.set_footer(text="Say brb back here when you return, or wait for the timer.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="brbzone")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @app_commands.describe(timezone_name='IANA name, e.g. America/New_York, Europe/London, UTC')
    async def brb_zone(self, ctx: commands.Context, *, timezone_name: str):
        """Set the guild timezone for `brb at 3:30pm` / `until 15:30`."""
        name = timezone_name.strip()
        try:
            ZoneInfo(name)
        except ZoneInfoNotFoundError:
            await ctx.send(
                f"Unknown timezone `{name}`. Use an IANA name like **America/New_York** or **UTC**."
            )
            return
        await self.config.guild(ctx.guild).timezone.set(name)
        await ctx.send(f"Guild BRB timezone set to **`{name}`**.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if not message.mentions:
            return
        try:
            prefixes = await self.bot.get_prefix(message)
        except Exception:
            prefixes = ()
        if isinstance(prefixes, str):
            prefixes = (prefixes,)
        if message.content:
            for p in prefixes:
                if p and message.content.startswith(p):
                    return

        now_ts = _utc_now().timestamp()
        guild = message.guild
        for mentioned in message.mentions:
            if mentioned.bot:
                continue
            if mentioned.id == message.author.id:
                continue
            until = await self.config.member(mentioned).brb_until()
            if until is None or now_ts >= float(until):
                continue

            key = (guild.id, mentioned.id, message.channel.id)
            last = self._ping_cd.get(key, 0.0)
            if now_ts - last < 45.0:
                continue
            self._ping_cd[key] = now_ts

            try:
                await message.channel.send(
                    f"{random.choice(_DISMISSIVE)}\n— *{mentioned.display_name} is on BRB*",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except discord.HTTPException:
                pass