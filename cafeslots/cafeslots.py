#
# Café Slots — three reels, zero real money, maximum pastry energy.
#

from __future__ import annotations

import asyncio
import random
import time
from typing import Dict, List, Optional, Tuple

import discord
from discord import Embed
from redbot.core import Config, commands

# (emoji, name, weight) — lower weight = rarer
_SYMBOLS: List[Tuple[str, str, int]] = [
    ("🫘", "Bean", 30),
    ("☕", "Cup", 25),
    ("🥐", "Croissant", 20),
    ("💨", "Steam", 15),
    ("🍬", "Sugar", 12),
    ("⚙️", "Grinder", 8),
    ("✨", "Golden Latte", 3),
]

# Three-of-a-kind payouts by symbol name
_PAYOUTS: Dict[str, int] = {
    "Bean": 15,
    "Cup": 25,
    "Croissant": 40,
    "Steam": 60,
    "Sugar": 80,
    "Grinder": 120,
    "Golden Latte": 250,
}

_SPIN_COOLDOWN = 20  # seconds


def _weighted_symbol() -> Tuple[str, str]:
    pool = []
    for emoji, name, weight in _SYMBOLS:
        pool.extend([(emoji, name)] * weight)
    return random.choice(pool)


def _score_reels(reels: List[Tuple[str, str]]) -> Tuple[int, str]:
    names = [r[1] for r in reels]
    emojis = " | ".join(r[0] for r in reels)
    if names[0] == names[1] == names[2]:
        pay = _PAYOUTS[names[0]]
        if names[0] == "Golden Latte":
            return pay, f"{emojis}\n**JACKPOT!** Triple Golden Latte. The café erupts."
        return pay, f"{emojis}\nTriple **{names[0]}** — +{pay} tip points."
    if names[0] == names[1] or names[1] == names[2] or names[0] == names[2]:
        return 5, f"{emojis}\nPair! Consolation croissant worth **5** tip points."
    # Near-miss: two golden adjacent feel
    if "Golden Latte" in names:
        return 2, f"{emojis}\nGolden glint… so close. **2** pity points."
    return 0, f"{emojis}\nNothing. The grinder judges you in silence."


def _paytable_text() -> str:
    lines = [f"{e} {n}: **{_PAYOUTS[n]}**" for e, n, _ in _SYMBOLS]
    lines.append("Any pair: **5** · Golden tease: **2**")
    return " · ".join(lines[:4]) + "\n" + " · ".join(lines[4:])


class SlotsView(discord.ui.View):
    def __init__(self, cog: "Cafeslots", player_id: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.player_id = player_id
        self.spinning = False
        self.message: Optional[discord.Message] = None
        self.last_result = "Press **Spin** to pull the lever."
        self.last_payout = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "These reels are reserved. Run `/slots` for your own machine.",
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

    def _embed(self, title: str = "🎰 Café Slots") -> Embed:
        emb = Embed(
            title=title,
            description=self.last_result,
            color=0x8B4513,
        )
        if self.last_payout:
            emb.add_field(name="Last Payout", value=f"**{self.last_payout}** tip points", inline=True)
        emb.set_footer(text=_paytable_text())
        return emb

    @discord.ui.button(label="Spin", style=discord.ButtonStyle.success, emoji="🎲")
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.spinning:
            await interaction.response.send_message("Reels still spinning…", ephemeral=True)
            return

        ok, wait = await self.cog._check_cooldown(interaction.user.id)
        if not ok:
            await interaction.response.send_message(
                f"Cool the machine — try again in **{wait}s**.",
                ephemeral=True,
            )
            return

        self.spinning = True
        button.disabled = True
        await interaction.response.edit_message(
            embed=Embed(title="🎰 Café Slots", description="🫘 | ☕ | 🥐\n*Whirrr…*", color=0x8B4513),
            view=self,
        )

        for frame in ("💨 | ⚙️ | 🍬", "🥐 | ✨ | 🫘", "☕ | 💨 | ⚙️"):
            await asyncio.sleep(0.45)
            try:
                await interaction.edit_original_response(
                    embed=Embed(
                        title="🎰 Café Slots",
                        description=f"{frame}\n*Clack…*",
                        color=0x8B4513,
                    ),
                    view=self,
                )
            except discord.HTTPException:
                break

        reels = [_weighted_symbol() for _ in range(3)]
        payout, text = _score_reels(reels)
        self.last_result = text
        self.last_payout = payout
        await self.cog._record_spin(interaction.guild, interaction.user, payout)
        await self.cog._set_cooldown(interaction.user.id)

        self.spinning = False
        button.disabled = False
        try:
            await interaction.edit_original_response(embed=self._embed(), view=self)
        except discord.HTTPException:
            pass


class Cafeslots(commands.Cog):
    """Café-themed slot machine with tip-point scores (no real currency)."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xC4FE5107, force_registration=True)
        self.config.register_member(spins=0, biggest_payout=0, total_payout=0)
        self._cooldowns: Dict[int, float] = {}

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()
        self._cooldowns.pop(user_id, None)

    async def _check_cooldown(self, user_id: int) -> Tuple[bool, int]:
        until = self._cooldowns.get(user_id, 0)
        now = time.monotonic()
        if now < until:
            return False, int(until - now) + 1
        return True, 0

    async def _set_cooldown(self, user_id: int) -> None:
        self._cooldowns[user_id] = time.monotonic() + _SPIN_COOLDOWN

    async def _record_spin(
        self, guild: Optional[discord.Guild], user: discord.abc.User, payout: int
    ) -> None:
        if guild is None:
            return
        member = guild.get_member(user.id)
        if member is None:
            return
        conf = self.config.member(member)
        spins = await conf.spins()
        await conf.spins.set(spins + 1)
        total = await conf.total_payout()
        await conf.total_payout.set(total + payout)
        biggest = await conf.biggest_payout()
        if payout > biggest:
            await conf.biggest_payout.set(payout)

    @commands.hybrid_command(name="slots", aliases=["cafeslots"])
    @commands.guild_only()
    async def slots(self, ctx: commands.Context):
        """Play the café slot machine. Tip points are for bragging only."""
        view = SlotsView(self, ctx.author.id)
        msg = await ctx.send(embed=view._embed(), view=view)
        view.message = msg

    @commands.hybrid_command(name="slotsboard", aliases=["slotboard"])
    @commands.guild_only()
    async def slotsboard(self, ctx: commands.Context):
        """Leaderboard: biggest single payout and most spins."""
        members = ctx.guild.members
        rows = []
        for m in members:
            if m.bot:
                continue
            data = await self.config.member(m).all()
            if data["spins"] == 0:
                continue
            rows.append((m.display_name, data["biggest_payout"], data["spins"], data["total_payout"]))

        if not rows:
            await ctx.send("No spins yet. Someone pull the lever with `/slots`.")
            return

        by_big = sorted(rows, key=lambda r: r[1], reverse=True)[:5]
        by_spins = sorted(rows, key=lambda r: r[2], reverse=True)[:5]

        emb = Embed(title="☕ Café Slots Board", color=0x8B4513)
        emb.add_field(
            name="Biggest Single Payout",
            value="\n".join(f"**{n}** — {b}" for n, b, _, _ in by_big) or "—",
            inline=False,
        )
        emb.add_field(
            name="Most Spins",
            value="\n".join(f"**{n}** — {s} spins" for n, _, s, _ in by_spins) or "—",
            inline=False,
        )
        await ctx.send(embed=emb)
