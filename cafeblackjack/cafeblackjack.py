#
# Blackjack — Café Dealer, Hit / Stand / Double buttons. No real stakes.
#

from __future__ import annotations

import random
from typing import List, Optional

import discord
from discord import Embed
from redbot.core import Config, commands

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def _new_deck() -> List[str]:
    deck = [f"{r}{s}" for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def _card_value(card: str) -> int:
    rank = card[:-1]
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)


def _hand_total(hand: List[str]) -> int:
    total = sum(_card_value(c) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def _hand_str(hand: List[str], hide_first: bool = False) -> str:
    if hide_first and hand:
        return "🂠 " + " ".join(hand[1:])
    return " ".join(hand) if hand else "—"


def _is_blackjack(hand: List[str]) -> bool:
    return len(hand) == 2 and _hand_total(hand) == 21


class BlackjackView(discord.ui.View):
    def __init__(self, cog: "CafeBlackjack", player_id: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.player_id = player_id
        self.deck = _new_deck()
        self.player: List[str] = []
        self.dealer: List[str] = []
        self.doubled = False
        self.first_action = True
        self.over = False
        self.result = ""
        self.outcome_key: Optional[str] = None  # wins | losses | pushes
        self.message: Optional[discord.Message] = None
        self._deal_initial()

    def _deal_initial(self) -> None:
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
        self.doubled = False
        self.first_action = True
        self.over = False
        self.result = ""
        self.outcome_key = None
        if _is_blackjack(self.player) or _is_blackjack(self.dealer):
            self._resolve()

    def _draw(self) -> str:
        if len(self.deck) < 10:
            self.deck = _new_deck()
        return self.deck.pop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "This table seat is taken. Deal yourself in with `/blackjack`.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        self._set_controls(finished=True)
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.HTTPException, discord.NotFound):
                pass

    def _set_controls(self, *, finished: bool) -> None:
        # Use attribute refs (no fixed custom_ids) so concurrent tables don't clash.
        self.hit.disabled = finished
        self.stand.disabled = finished
        self.double.disabled = finished or not self.first_action
        self.new_hand.disabled = not finished

    def _embed(self) -> Embed:
        hide = not self.over
        p_total = _hand_total(self.player)
        d_shown = _hand_total(self.dealer) if self.over else _card_value(self.dealer[0])
        emb = Embed(
            title="🃏 Café Blackjack",
            color=0x1B5E20 if not self.over else 0x37474F,
        )
        emb.add_field(
            name="Dealer",
            value=f"{_hand_str(self.dealer, hide_first=hide)}\n"
            + (f"Total: **{_hand_total(self.dealer)}**" if self.over else f"Showing: **{d_shown}**"),
            inline=False,
        )
        emb.add_field(
            name="You",
            value=f"{_hand_str(self.player)}\nTotal: **{p_total}**"
            + (" *(doubled)*" if self.doubled else ""),
            inline=False,
        )
        if self.result:
            emb.add_field(name="Result", value=self.result, inline=False)
        else:
            emb.set_footer(text="Café Dealer stands on 17. Soft aces welcome.")
        return emb

    def _resolve(self) -> str:
        """Resolve end-of-hand; sets self.over/result/outcome_key. Returns wins|losses|pushes."""
        self.over = True
        p = _hand_total(self.player)
        p_bj = _is_blackjack(self.player)
        d_bj = _is_blackjack(self.dealer)

        if p_bj and d_bj:
            self.result = "Push — double blackjack. The espresso machine sighs."
            self.outcome_key = "pushes"
            return self.outcome_key
        if p_bj:
            self.result = "**Blackjack!** 3:2 bragging rights. The Café Dealer tips their hat."
            self.outcome_key = "wins"
            return self.outcome_key
        if d_bj:
            self.result = "Dealer blackjack. You lose. Steam everywhere."
            self.outcome_key = "losses"
            return self.outcome_key

        if p > 21:
            self.result = f"Bust at **{p}**. You lose. Someone burns the toast."
            self.outcome_key = "losses"
            return self.outcome_key

        while _hand_total(self.dealer) < 17:
            self.dealer.append(self._draw())
        d = _hand_total(self.dealer)

        if d > 21:
            self.result = f"Dealer busts at **{d}**. You win. Free refill energy."
            self.outcome_key = "wins"
        elif p > d:
            self.result = f"You win **{p}** vs **{d}**. Clean pour."
            self.outcome_key = "wins"
        elif p < d:
            self.result = f"You lose **{p}** vs **{d}**. House blend prevails."
            self.outcome_key = "losses"
        else:
            self.result = f"Push **{p}**–**{d}**. Split the pastry."
            self.outcome_key = "pushes"
        return self.outcome_key

    async def _resolve_and_edit(self, interaction: discord.Interaction) -> None:
        key = self._resolve()
        self._set_controls(finished=True)
        if interaction.guild:
            await self.cog._bump_stat(interaction.guild, interaction.user.id, key)
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🃏")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.over:
            await interaction.response.send_message("Hand is over — deal a new one.", ephemeral=True)
            return
        self.first_action = False
        self.player.append(self._draw())
        if _hand_total(self.player) > 21:
            self.over = True
            self.outcome_key = "losses"
            self.result = f"Bust at **{_hand_total(self.player)}**. You lose."
            self._set_controls(finished=True)
            if interaction.guild:
                await self.cog._bump_stat(interaction.guild, interaction.user.id, "losses")
            await interaction.response.edit_message(embed=self._embed(), view=self)
            return
        self._set_controls(finished=False)
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="🛑")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.over:
            await interaction.response.send_message("Hand is over — deal a new one.", ephemeral=True)
            return
        await self._resolve_and_edit(interaction)

    @discord.ui.button(label="Double", style=discord.ButtonStyle.danger, emoji="✌️")
    async def double(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.over:
            await interaction.response.send_message("Hand is over — deal a new one.", ephemeral=True)
            return
        if not self.first_action:
            await interaction.response.send_message("Double only on your first action.", ephemeral=True)
            return
        self.first_action = False
        self.doubled = True
        self.player.append(self._draw())
        if _hand_total(self.player) > 21:
            self.over = True
            self.outcome_key = "losses"
            self.result = f"Doubled into a bust (**{_hand_total(self.player)}**). Bold. Costly. You lose."
            self._set_controls(finished=True)
            if interaction.guild:
                await self.cog._bump_stat(interaction.guild, interaction.user.id, "losses")
            await interaction.response.edit_message(embed=self._embed(), view=self)
            return
        await self._resolve_and_edit(interaction)

    @discord.ui.button(label="New Hand", style=discord.ButtonStyle.success, emoji="🔁", disabled=True)
    async def new_hand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.over:
            await interaction.response.send_message("Finish this hand first.", ephemeral=True)
            return
        self.deck = _new_deck()
        self._deal_initial()
        if self.over and self.outcome_key:
            self._set_controls(finished=True)
            if interaction.guild:
                await self.cog._bump_stat(interaction.guild, interaction.user.id, self.outcome_key)
        else:
            self._set_controls(finished=False)
        await interaction.response.edit_message(embed=self._embed(), view=self)


class CafeBlackjack(commands.Cog):
    """Button blackjack against the Café Dealer. Tracks wins/losses/pushes."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xB1AC1001, force_registration=True)
        self.config.register_member(wins=0, losses=0, pushes=0)

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()

    async def _bump_stat(self, guild: discord.Guild, user_id: int, key: str) -> None:
        conf = self.config.member_from_ids(guild.id, user_id)
        val = await conf.get_raw(key, default=0)
        await conf.set_raw(key, value=val + 1)

    @commands.hybrid_group(name="blackjack", invoke_without_command=True)
    @commands.guild_only()
    async def blackjack(self, ctx: commands.Context):
        """Play blackjack vs the Café Dealer."""
        if ctx.invoked_subcommand is not None:
            return
        view = BlackjackView(self, ctx.author.id)
        if view.over and view.outcome_key:
            view._set_controls(finished=True)
            await self._bump_stat(ctx.guild, ctx.author.id, view.outcome_key)
        else:
            view._set_controls(finished=False)
        msg = await ctx.send(embed=view._embed(), view=view)
        view.message = msg

    @blackjack.command(name="stats")
    @commands.guild_only()
    async def blackjack_stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Show blackjack win/loss/push stats."""
        target = member or ctx.author
        data = await self.config.member(target).all()
        total = data["wins"] + data["losses"] + data["pushes"]
        emb = Embed(
            title=f"🃏 Stats — {target.display_name}",
            color=0x1B5E20,
        )
        emb.add_field(name="Wins", value=str(data["wins"]))
        emb.add_field(name="Losses", value=str(data["losses"]))
        emb.add_field(name="Pushes", value=str(data["pushes"]))
        if total:
            rate = data["wins"] / total * 100
            emb.set_footer(text=f"{total} hands · {rate:.1f}% win rate (pushes count)")
        else:
            emb.set_footer(text="No hands yet — `/blackjack` to deal in.")
        await ctx.send(embed=emb)
