#
# Power Level — DBZ-style scouter readings with café steam on the lens.
#

from __future__ import annotations

import random
import time
from typing import List, Optional, Tuple

import discord
from discord import Embed
from redbot.core import Config, commands

_FLAVOR: List[str] = [
    "Scouter fogged by espresso steam — reading still locked.",
    "The dial squealed like a milk pitcher under pressure.",
    "Someone spilled oat milk on the lens. Accuracy… interpretive.",
    "Power spike detected near the pastry case.",
    "The scouter whispered *over nine thousand beans*.",
    "Calibration done against a double ristretto. Bold choice.",
    "Static crackled. The café Wi‑Fi is jealous.",
    "Reading confirmed. The barista nodded once and said nothing.",
]

_RANKS: List[Tuple[int, str]] = [
    (0, "Earthling (Decaf Timeline)"),
    (100, "Farm Kid with a Dream"),
    (1_000, "Local Tournament Contender"),
    (5_000, "City Block Menace"),
    (9_001, "Over Nine Thousand"),
    (50_000, "Super Saiyan (Steamed)"),
    (150_000, "Super Saiyan 2 (Extra Foam)"),
    (400_000, "Super Saiyan 3 (Hair Tax)"),
    (1_000_000, "Super Saiyan God (Single Origin)"),
    (5_000_000, "Blue (Cold Foam Aura)"),
    (20_000_000, "Ultra Instinct (Eyes Closed, Still Pouring)"),
    (100_000_000, "Angel Tier (Tips in Light)"),
]


def _roll_power() -> int:
    """Weighted power level: common mid-tier, rare god spikes."""
    roll = random.random()
    if roll < 0.02:
        return random.randint(20_000_000, 250_000_000)
    if roll < 0.08:
        return random.randint(1_000_000, 19_999_999)
    if roll < 0.20:
        return random.randint(50_000, 999_999)
    if roll < 0.45:
        return random.randint(5_000, 49_999)
    if roll < 0.75:
        return random.randint(500, 4_999)
    return random.randint(5, 499)


def _rank_for(level: int) -> str:
    name = _RANKS[0][1]
    for threshold, rank in _RANKS:
        if level >= threshold:
            name = rank
        else:
            break
    return name


def _fmt(n: int) -> str:
    return f"{n:,}"


class PowerLevelView(discord.ui.View):
    def __init__(self, cog: "Powerlevel", invoker_id: int, target: discord.abc.User, level: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.invoker_id = invoker_id
        self.target = target
        self.level = level
        self._last_rescan = 0.0
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "This scouter is calibrated to someone else. Run `/powerlevel` for your own reading.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.HTTPException, discord.NotFound):
                pass

    def _embed(self, *, extra: Optional[str] = None) -> Embed:
        emb = Embed(
            title="📡 Scouter Reading",
            description=(
                f"**{self.target.display_name}**\n"
                f"Power Level: **{_fmt(self.level)}**\n"
                f"Saiyan Rank: *{_rank_for(self.level)}*"
            ),
            color=0xF4C430,
        )
        emb.set_thumbnail(url=self.target.display_avatar.url)
        emb.set_footer(text=random.choice(_FLAVOR))
        if extra:
            emb.add_field(name="Scan Note", value=extra, inline=False)
        return emb

    @discord.ui.button(label="Rescan", style=discord.ButtonStyle.primary, emoji="🔄")
    async def rescan(self, interaction: discord.Interaction, button: discord.ui.Button):
        now = time.monotonic()
        if now - self._last_rescan < 8:
            await interaction.response.send_message(
                "Scouter overheating. Wait a few seconds before rescanning.",
                ephemeral=True,
            )
            return
        self._last_rescan = now
        self.level = _roll_power()
        await self.cog._maybe_record(interaction.guild, self.target, self.level)
        await interaction.response.edit_message(
            embed=self._embed(extra="Fresh scan complete. Try not to flex too hard."),
            view=self,
        )

    @discord.ui.button(label="Saiyan Rank", style=discord.ButtonStyle.secondary, emoji="🥋")
    async def saiyan_rank(self, interaction: discord.Interaction, button: discord.ui.Button):
        ladder = "\n".join(
            f"{'➤' if self.level >= t else '·'} **{_fmt(t)}+** — {name}" for t, name in _RANKS
        )
        emb = self._embed()
        emb.add_field(name="Rank Ladder", value=ladder, inline=False)
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="Compare", style=discord.ButtonStyle.success, emoji="⚔️")
    async def compare(self, interaction: discord.Interaction, button: discord.ui.Button):
        other = _roll_power()
        if self.level > other:
            verdict = (
                f"You crush a mystery rival at **{_fmt(other)}**. "
                f"Margin: **{_fmt(self.level - other)}**."
            )
        elif self.level < other:
            verdict = (
                f"A mystery rival hits **{_fmt(other)}**. "
                f"You're short by **{_fmt(other - self.level)}**. Train harder. Sip faster."
            )
        else:
            verdict = f"Dead even at **{_fmt(self.level)}**. The universe shrugs."
        await interaction.response.edit_message(embed=self._embed(extra=verdict), view=self)


class Powerlevel(commands.Cog):
    """DBZ-style power level scanner with interactive scouter buttons."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xDB750001, force_registration=True)
        self.config.register_guild(
            highest_user=None,
            highest_level=0,
            highest_name=None,
        )
        self.config.register_global(
            highest_user=None,
            highest_level=0,
            highest_name=None,
        )

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        g = await self.config.highest_user()
        if g == user_id:
            await self.config.highest_user.set(None)
            await self.config.highest_level.set(0)
            await self.config.highest_name.set(None)
        for guild in self.bot.guilds:
            if await self.config.guild(guild).highest_user() == user_id:
                await self.config.guild(guild).highest_user.set(None)
                await self.config.guild(guild).highest_level.set(0)
                await self.config.guild(guild).highest_name.set(None)

    async def _maybe_record(
        self, guild: Optional[discord.Guild], user: discord.abc.User, level: int
    ) -> None:
        global_best = await self.config.highest_level()
        if level > global_best:
            await self.config.highest_level.set(level)
            await self.config.highest_user.set(user.id)
            await self.config.highest_name.set(user.display_name)
        if guild is not None:
            conf = self.config.guild(guild)
            if level > await conf.highest_level():
                await conf.highest_level.set(level)
                await conf.highest_user.set(user.id)
                await conf.highest_name.set(user.display_name)

    @commands.hybrid_command(name="powerlevel", aliases=["scouter"])
    async def powerlevel(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Scan a DBZ-style power level for yourself or another member."""
        target = user or ctx.author
        if target.bot:
            await ctx.send("Bots run on firmware, not ki. The scouter refuses.")
            return

        level = _roll_power()
        await self._maybe_record(ctx.guild, target, level)

        view = PowerLevelView(self, ctx.author.id, target, level)
        msg = await ctx.send(embed=view._embed(), view=view)
        view.message = msg

    @commands.hybrid_command(name="powerrecord")
    async def powerrecord(self, ctx: commands.Context):
        """Show the highest power level recorded (guild + global)."""
        emb = Embed(title="🏆 Scouter Hall of Fame", color=0xF4C430)
        g_level = await self.config.highest_level()
        g_name = await self.config.highest_name()
        if g_level and g_name:
            emb.add_field(
                name="Global",
                value=f"**{g_name}** — {_fmt(g_level)} ({_rank_for(g_level)})",
                inline=False,
            )
        else:
            emb.add_field(name="Global", value="No readings yet.", inline=False)

        if ctx.guild:
            conf = self.config.guild(ctx.guild)
            level = await conf.highest_level()
            name = await conf.highest_name()
            if level and name:
                emb.add_field(
                    name="This Server",
                    value=f"**{name}** — {_fmt(level)} ({_rank_for(level)})",
                    inline=False,
                )
            else:
                emb.add_field(name="This Server", value="No readings yet.", inline=False)

        await ctx.send(embed=emb)
