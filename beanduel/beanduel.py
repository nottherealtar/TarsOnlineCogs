#
# Bean Duel — Espresso / Latte / Cold Brew RPS with Accept / Decline.
#

from __future__ import annotations

import random
from typing import Dict, Optional

import discord
from discord import Embed
from redbot.core import Config, commands

# RPS triangle: Espresso > Latte > Cold Brew > Espresso
CHOICES = {
    "espresso": {"beats": "latte", "emoji": "☕", "label": "Espresso"},
    "latte": {"beats": "coldbrew", "emoji": "🥛", "label": "Latte"},
    "coldbrew": {"beats": "espresso", "emoji": "🧊", "label": "Cold Brew"},
}

_WIN_LINES = [
    "{winner} steams {loser} into submission. The pastry case applauds.",
    "{winner} pulls a cleaner shot. {loser} is under-extracted.",
    "{winner} wins. {loser} must bus the metaphorical tables.",
    "Victory for {winner}. {loser}'s foam collapsed.",
]

_TIE_LINES = [
    "Same brew. The universe shrugs and refills both cups.",
    "Dead even. Split the last croissant.",
    "Mirror pour. Rematch energy incoming.",
]


def _outcome(a: str, b: str) -> str:
    if a == b:
        return "tie"
    if CHOICES[a]["beats"] == b:
        return "a"
    return "b"


class PickView(discord.ui.View):
    def __init__(self, duel: "ChallengeView"):
        super().__init__(timeout=60)
        self.duel = duel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        uid = interaction.user.id
        if uid not in (self.duel.challenger_id, self.duel.challengee_id):
            await interaction.response.send_message("Not your duel.", ephemeral=True)
            return False
        if uid in self.duel.picks:
            await interaction.response.send_message("You already locked in a brew.", ephemeral=True)
            return False
        return True

    async def _pick(self, interaction: discord.Interaction, choice: str) -> None:
        self.duel.picks[interaction.user.id] = choice
        await interaction.response.send_message(
            f"Locked in **{CHOICES[choice]['label']}**. Waiting on your rival…",
            ephemeral=True,
        )
        if len(self.duel.picks) == 2:
            await self.duel.reveal()

    @discord.ui.button(label="Espresso", style=discord.ButtonStyle.danger, emoji="☕")
    async def espresso(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._pick(interaction, "espresso")

    @discord.ui.button(label="Latte", style=discord.ButtonStyle.primary, emoji="🥛")
    async def latte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._pick(interaction, "latte")

    @discord.ui.button(label="Cold Brew", style=discord.ButtonStyle.success, emoji="🧊")
    async def coldbrew(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._pick(interaction, "coldbrew")


class ChallengeView(discord.ui.View):
    def __init__(
        self,
        cog: "Beanduel",
        challenger: discord.Member,
        challengee: discord.Member,
    ):
        super().__init__(timeout=60)
        self.cog = cog
        self.challenger_id = challenger.id
        self.challengee_id = challengee.id
        self.challenger = challenger
        self.challengee = challengee
        self.picks: Dict[int, str] = {}
        self.message: Optional[discord.Message] = None
        self.pick_view: Optional[PickView] = None
        self.resolved = False

    async def on_timeout(self) -> None:
        if self.resolved:
            return
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    content=None,
                    embed=Embed(
                        title="☕ Bean Duel Expired",
                        description="Nobody answered. The beans went stale.",
                        color=0x795548,
                    ),
                    view=self,
                )
            except (discord.HTTPException, discord.NotFound):
                pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challengee_id:
            await interaction.response.send_message(
                "Only the challenged can accept.", ephemeral=True
            )
            return
        self.resolved = True
        for item in self.children:
            item.disabled = True
        self.pick_view = PickView(self)
        self.message = interaction.message
        emb = Embed(
            title="☕ Bean Duel — Choose Your Brew",
            description=(
                f"{self.challenger.mention} vs {self.challengee.mention}\n\n"
                "**Espresso** beats **Latte**\n"
                "**Latte** beats **Cold Brew**\n"
                "**Cold Brew** beats **Espresso**\n\n"
                "Both players: pick below (your choice is private)."
            ),
            color=0x6F4E37,
        )
        await interaction.response.edit_message(embed=emb, view=self.pick_view)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challengee_id:
            await interaction.response.send_message(
                "Only the challenged can decline.", ephemeral=True
            )
            return
        self.resolved = True
        for item in self.children:
            item.disabled = True
        emb = Embed(
            title="☕ Bean Duel Declined",
            description=f"{self.challengee.display_name} walked away from the counter.",
            color=0x795548,
        )
        await interaction.response.edit_message(embed=emb, view=self)

    async def reveal(self) -> None:
        a = self.picks[self.challenger_id]
        b = self.picks[self.challengee_id]
        result = _outcome(a, b)
        a_l = f"{CHOICES[a]['emoji']} {CHOICES[a]['label']}"
        b_l = f"{CHOICES[b]['emoji']} {CHOICES[b]['label']}"

        if result == "tie":
            text = random.choice(_TIE_LINES)
            color = 0xFFC107
        elif result == "a":
            text = random.choice(_WIN_LINES).format(
                winner=self.challenger.display_name, loser=self.challengee.display_name
            )
            color = 0x4CAF50
            await self.cog._record(self.challenger, self.challengee, winner_id=self.challenger_id)
        else:
            text = random.choice(_WIN_LINES).format(
                winner=self.challengee.display_name, loser=self.challenger.display_name
            )
            color = 0x4CAF50
            await self.cog._record(self.challenger, self.challengee, winner_id=self.challengee_id)

        emb = Embed(
            title="☕ Bean Duel — Reveal",
            description=(
                f"**{self.challenger.display_name}:** {a_l}\n"
                f"**{self.challengee.display_name}:** {b_l}\n\n{text}"
            ),
            color=color,
        )
        rematch = RematchView(self.cog, self.challenger, self.challengee)
        if self.message:
            try:
                await self.message.edit(embed=emb, view=rematch)
            except (discord.HTTPException, discord.NotFound):
                pass
        if self.pick_view:
            self.pick_view.stop()


class RematchView(discord.ui.View):
    def __init__(
        self, cog: "Beanduel", challenger: discord.Member, challengee: discord.Member
    ):
        super().__init__(timeout=60)
        self.cog = cog
        self.challenger = challenger
        self.challengee = challengee

    @discord.ui.button(label="Rematch", style=discord.ButtonStyle.primary, emoji="🔁")
    async def rematch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.challenger.id, self.challengee.id):
            await interaction.response.send_message("Spectators can't rematch.", ephemeral=True)
            return
        # Swap roles: clicker challenges the other
        if interaction.user.id == self.challenger.id:
            new_c, new_e = self.challenger, self.challengee
        else:
            new_c, new_e = self.challengee, self.challenger
        view = ChallengeView(self.cog, new_c, new_e)
        emb = Embed(
            title="☕ Bean Duel Rematch",
            description=f"{new_c.mention} challenges {new_e.mention} again!\n{new_e.mention}: Accept or Decline.",
            color=0x6F4E37,
        )
        await interaction.response.edit_message(embed=emb, view=view)
        view.message = interaction.message


class Beanduel(commands.Cog):
    """Challenge members to Espresso / Latte / Cold Brew duels."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xBEA4D001, force_registration=True)
        self.config.register_member(wins=0, losses=0)

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()

    async def _record(
        self, a: discord.Member, b: discord.Member, *, winner_id: int
    ) -> None:
        winner = a if a.id == winner_id else b
        loser = b if a.id == winner_id else a
        w = self.config.member(winner)
        l = self.config.member(loser)
        await w.wins.set(await w.wins() + 1)
        await l.losses.set(await l.losses() + 1)

    @commands.hybrid_command(name="beanduel")
    @commands.guild_only()
    async def beanduel(self, ctx: commands.Context, opponent: discord.Member):
        """Challenge someone to a café brew duel (RPS)."""
        if opponent.id == ctx.author.id:
            await ctx.send("You can't duel your own reflection. The mirror already won.")
            return
        if opponent.bot:
            await ctx.send("Bots don't drink coffee. They drink uptime.")
            return

        view = ChallengeView(self, ctx.author, opponent)
        emb = Embed(
            title="☕ Bean Duel Challenge",
            description=(
                f"{ctx.author.mention} challenges {opponent.mention}!\n"
                f"{opponent.mention}: **Accept** or **Decline** within 60s."
            ),
            color=0x6F4E37,
        )
        msg = await ctx.send(embed=emb, view=view)
        view.message = msg

    @commands.hybrid_command(name="beanduelboard")
    @commands.guild_only()
    async def beanduel_board(self, ctx: commands.Context):
        """Guild bean-duel win/loss leaderboard."""
        rows = []
        for m in ctx.guild.members:
            if m.bot:
                continue
            data = await self.config.member(m).all()
            if data["wins"] == 0 and data["losses"] == 0:
                continue
            rows.append((m.display_name, data["wins"], data["losses"]))
        if not rows:
            await ctx.send("No duels recorded yet. `/beanduel @user` to start something.")
            return
        rows.sort(key=lambda r: (r[1], -r[2]), reverse=True)
        top = rows[:10]
        lines = [f"**{n}** — {w}W / {l}L" for n, w, l in top]
        emb = Embed(title="☕ Bean Duel Board", description="\n".join(lines), color=0x6F4E37)
        await ctx.send(embed=emb)
