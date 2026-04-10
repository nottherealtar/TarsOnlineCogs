#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

import discord
from discord import Embed, app_commands
from redbot.core import Config, commands

COFFEE_GIF = (
    "https://cdn.discordapp.com/attachments/1170989523895865424/1172244571359551498/"
    "YourCoffee.gif?ex=655f9cd5&is=654d27d5&hm=cda30beb01cd668d165445ba74c2faed96f595cdef0445d9dca77343a37a2579&"
)

# (minimum best-streak to earn title, display name) — ascending thresholds
TITLE_LADDER: List[Tuple[int, str]] = [
    (0, "Decaf Outsider"),
    (1, "Bean Apprentice"),
    (3, "Pour-Over Pupil"),
    (7, "Latte Luminary"),
    (14, "Cortado Cultist"),
    (30, "Moka Mystic"),
    (60, "Siphon Sage"),
    (100, "Espresso Eldritch"),
]


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def title_for_best_streak(best: int) -> Tuple[str, Optional[int]]:
    """Current title from lifetime best streak, and next threshold (or None if maxed)."""
    name = TITLE_LADDER[0][1]
    next_need: Optional[int] = None
    for i, (need, tier_name) in enumerate(TITLE_LADDER):
        if best >= need:
            name = tier_name
        else:
            next_need = need
            break
    return name, next_need


class Coffee(commands.Cog):
    """Virtual coffee orders and a guild-scoped daily check-in streak with titles & leaderboards."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xC0FFEE01, force_registration=True)
        self.config.register_member(
            last_checkin_date=None,
            streak=0,
            best_streak=0,
            total_checkins=0,
        )

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()

    @commands.hybrid_group(name="coffee", invoke_without_command=True)
    async def coffee(self, ctx: commands.Context):
        """Coffee lounge: orders, daily check-ins, streaks, and boards."""
        # No fallback="order" here: discord.py would register slash "order" twice
        # (fallback + @coffee.command(order)) → CommandAlreadyRegistered.
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @coffee.command(name="order")
    async def coffee_order(self, ctx, user: Optional[discord.User] = None):
        """Pour a virtual coffee for yourself or someone else (classic GIF)."""
        target = user or ctx.author
        embed = Embed(title=f"Coffee order for {target.name} ☕", color=0x8B4513)
        embed.set_image(url=COFFEE_GIF)
        embed.set_footer(text="Enjoy your coffee from Tars Online Cafe!")
        await ctx.send(embed=embed)

    @coffee.command(name="checkin")
    @commands.guild_only()
    async def coffee_checkin(self, ctx: commands.Context):
        """Claim your daily brew. Keeps a streak in this server (UTC midnight rollover)."""
        if ctx.author.bot:
            await ctx.send("Bots run on oil, not beans. ☕")
            return

        member = ctx.author
        conf = self.config.member(member)
        today = _utc_today()
        today_s = today.isoformat()
        last_s = await conf.last_checkin_date()
        streak_was = await conf.streak()
        best = await conf.best_streak()
        total = await conf.total_checkins()

        if last_s == today_s:
            title, next_need = title_for_best_streak(best)
            embed = Embed(
                title="Already brewed today ☕",
                description=f"You already checked in, {member.display_name}. Come back after **UTC midnight** for the next cup.",
                color=0x6F4E37,
            )
            embed.add_field(name="Current streak", value=str(streak_was), inline=True)
            embed.add_field(name="Best streak", value=str(best), inline=True)
            embed.add_field(name="Total check-ins", value=str(total), inline=True)
            embed.add_field(name="Title", value=f"*{title}*", inline=False)
            if next_need is not None:
                embed.set_footer(text=f"Next title tier unlocks at **{next_need}** best streak.")
            await ctx.send(embed=embed)
            return

        if last_s:
            try:
                last_d = date.fromisoformat(last_s)
            except ValueError:
                last_d = None
        else:
            last_d = None

        if last_d == today - timedelta(days=1):
            new_streak = streak_was + 1
        else:
            new_streak = 1

        new_best = max(best, new_streak)
        new_total = total + 1

        await conf.last_checkin_date.set(today_s)
        await conf.streak.set(new_streak)
        await conf.best_streak.set(new_best)
        await conf.total_checkins.set(new_total)

        title, next_need = title_for_best_streak(new_best)
        broken = last_d is not None and last_d < today - timedelta(days=1)

        embed = Embed(
            title="Daily brew claimed! ☕",
            description=f"**{member.display_name}** sips the sacred roast.",
            color=0x8B4513,
        )
        embed.add_field(name="Streak", value=f"**{new_streak}** day(s)", inline=True)
        embed.add_field(name="Best ever", value=str(new_best), inline=True)
        embed.add_field(name="Total visits", value=str(new_total), inline=True)
        embed.add_field(name="Title", value=f"*{title}*", inline=False)
        if broken and last_s:
            embed.add_field(
                name="Note",
                value="Streak reset — life happens. The beans still love you.",
                inline=False,
            )
        if next_need is not None and new_best < next_need:
            embed.set_footer(text=f"Reach **{next_need}** best streak for the next title.")
        await ctx.send(embed=embed)

    @coffee.command(name="streak", aliases=["status"])
    @commands.guild_only()
    async def coffee_streak(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Show your (or someone’s) streak, title, and totals in this server."""
        member = member or ctx.author
        if member.bot:
            await ctx.send("Bots don’t keep streaks here.")
            return

        conf = self.config.member(member)
        last_s = await conf.last_checkin_date()
        streak = await conf.streak()
        best = await conf.best_streak()
        total = await conf.total_checkins()
        title, next_need = title_for_best_streak(best)

        embed = Embed(
            title=f"☕ {member.display_name}",
            color=member.color if member.color.value else discord.Color.dark_gold(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Current streak", value=str(streak), inline=True)
        embed.add_field(name="Best streak", value=str(best), inline=True)
        embed.add_field(name="Total check-ins", value=str(total), inline=True)
        embed.add_field(name="Title", value=f"*{title}*", inline=False)
        if last_s:
            embed.add_field(name="Last check-in (UTC)", value=last_s, inline=False)
        if next_need is not None and best < next_need:
            embed.set_footer(text=f"Next title at **{next_need}** best streak ({next_need - best} to go).")
        await ctx.send(embed=embed)

    @coffee.command(name="titles", aliases=["ranks"])
    async def coffee_titles(self, ctx: commands.Context):
        """The full title ladder (from your best streak in any check-in server)."""
        lines = [f"**{need}+** best streak — *{name}*" for need, name in TITLE_LADDER]
        embed = Embed(
            title="Coffee title ladder",
            description="Titles come from your **lifetime best streak** in this server (not lost if you miss a day).",
            color=0x4B3621,
        )
        embed.add_field(name="Ranks", value="\n".join(lines), inline=False)
        embed.set_footer(text="Use /coffee checkin daily to climb.")
        await ctx.send(embed=embed)

    @coffee.command(name="board", aliases=["leaderboard", "lb"])
    @commands.guild_only()
    @app_commands.describe(metric="What to sort the board by")
    @app_commands.choices(
        metric=[
            app_commands.Choice(name="Current streak", value="streak"),
            app_commands.Choice(name="Best streak (record)", value="best"),
            app_commands.Choice(name="Total check-ins", value="total"),
        ]
    )
    async def coffee_board(self, ctx: commands.Context, metric: str = "streak"):
        """Top coffee regulars in this server."""
        metric = (metric or "streak").lower()
        if metric not in {"streak", "best", "total"}:
            metric = "streak"

        key_labels = {"streak": "current streak", "best": "best streak", "total": "total check-ins"}
        rows: List[Tuple[int, int, int, int, discord.Member]] = []
        for m in ctx.guild.members:
            if m.bot:
                continue
            cur = await self.config.member(m).streak()
            bst = await self.config.member(m).best_streak()
            tot = await self.config.member(m).total_checkins()
            if cur == 0 and bst == 0 and tot == 0:
                continue
            primary = {"streak": cur, "best": bst, "total": tot}[metric]
            rows.append((primary, cur, bst, tot, m))

        rows.sort(key=lambda x: (x[0], x[2], x[3]), reverse=True)
        rows = rows[:15]

        if not rows:
            await ctx.send("No one has checked in yet. Be the first with `/coffee checkin`.")
            return

        lines_out = []
        for i, (primary, cur, bst, tot, m) in enumerate(rows, start=1):
            if metric == "streak":
                lines_out.append(f"**{i}.** {m.display_name} — **{primary}** 🔥 (best {bst}, {tot} total)")
            elif metric == "best":
                lines_out.append(f"**{i}.** {m.display_name} — **{primary}** best (now {cur}, {tot} total)")
            else:
                lines_out.append(f"**{i}.** {m.display_name} — **{primary}** total (streak {cur}, best {bst})")

        embed = Embed(
            title=f"Coffee board — by {key_labels[metric]}",
            description="\n".join(lines_out),
            color=0xC4A484,
        )
        embed.set_footer(text="Tip: /coffee board and pick another metric from the menu.")
        await ctx.send(embed=embed)
