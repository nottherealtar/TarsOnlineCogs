#
# Roast or Toast — café-flavored praise and playful burns, button-driven.
#

from __future__ import annotations

import random
from typing import List, Optional

import discord
from discord import Embed
from redbot.core import commands

_ROASTS: List[str] = [
    "{t} orders iced coffee in a blizzard and calls it *personality*.",
    "{t}'s pour-over looks like they negotiated with the kettle and lost.",
    "If effort were crema, {t} would be a flat puddle.",
    "{t} microwaves leftover espresso. The beans filed a restraining order.",
    "{t}'s 'quick coffee run' has the runtime of a Tolkien sequel.",
    "Someone asked {t} for oat milk and they returned with a TED talk.",
    "{t} stirs with the wrong end of the spoon. Chronically.",
    "The sugar packets fear {t}. So does the tip jar. For different reasons.",
    "{t} seasonally confuses ' ristretto' with 'I tried'.",
    "{t}'s latte art is abstract — specifically, abstract regret.",
    "Wi‑Fi reconnects faster than {t} picks a drink.",
    "{t} said 'surprise me' and the barista aged three years.",
    "{t} treats the pastry case like a hostage negotiation.",
    "Decaf would still be too much commitment for {t} today.",
    "{t}'s favorite roast is whichever one is currently cold.",
    "If procrastination were a blend, {t} would be single-origin.",
    "{t} leaves the lid half-on. Chaos agent. Foam terrorist.",
    "The French press judged {t} and wrote a one-star review.",
    "{t} calls every brown liquid 'coffee' and every opinion 'fact'.",
    "{t}'s steam wand technique is… interpretive dance.",
    "Group orders dread {t}'s 'actually, can I change that?' arc.",
    "{t} tips in exposure. The register wept.",
    "{t} thinks cold foam is a personality type. Correct, unfortunately.",
    "Somewhere a clean portafilter is disappointed in {t}.",
    "{t} asked for 'the strong one' and meant the Wi‑Fi password.",
    "{t}'s mug collection is denser than their calendar.",
    "The grind size {t} chooses is 'vibes'. The extraction agrees to disagree.",
    "{t} once burned water. In a café. We don't talk about it.",
    "{t}'s 'I'll just have a small' is legally a medium with opinions.",
    "Even the loyalty card skipped {t}'s stamp. Self-care.",
]

_TOASTS: List[str] = [
    "{t} walks in and the ambient lighting improves by half a stop.",
    "{t}'s order is clear, kind, and somehow makes the line happier.",
    "If warmth were a pour, {t} would be the perfect bloom.",
    "{t} remembers names like a barista with a photographic palate.",
    "The room softens when {t} laughs. Acoustics confirmed.",
    "{t} is the human equivalent of a perfectly timed refill.",
    "Competence looks good on {t} — like a well-seasoned cast-iron skillet.",
    "{t} tips thoughtfully and exists like they mean it.",
    "Someone should study how {t} makes small talk feel non-threatening.",
    "{t} is the reason 'regular' became a compliment.",
    "Latte foam wishes it had {t}'s composure.",
    "{t} brings main-character calm without the plot armor arrogance.",
    "The pastry case would vote for {t}. Unanimously. Flakily.",
    "{t}'s presence is a free upgrade to the afternoon.",
    "If kindness had a loyalty card, {t} would be platinum.",
    "{t} listens like the good kind of silence — the productive kind.",
    "Baristas fight over who gets to make {t}'s drink. (Nice fight.)",
    "{t} is proof that 'chill' and 'dependable' can share a mug.",
    "The espresso machine hums approvingly near {t}. Science.",
    "{t} makes complicated orders sound like poetry, not a ransom note.",
    "Sunlight through the window? Nice. {t} arriving? Nicer.",
    "{t} has 'I brought enough for the table' energy even when empty-handed.",
    "A toast to {t}: may your mornings be extracted, not exhausted.",
    "{t} is the bookmark in a chaotic chapter. Correct page. Always.",
    "Somewhere a house blend is proud to be associated with {t}.",
    "{t}'s vibe is preheated. Ready. Welcoming.",
    "If patience were a roast profile, {t} would be the balanced medium.",
    "{t} makes the café feel like a third place, not a waiting room.",
    "Cheers to {t} — the rare person who improves the queue.",
    "{t}: walking soft launch of good news.",
]


class RoastToastView(discord.ui.View):
    def __init__(self, invoker_id: int, target: discord.abc.User):
        super().__init__(timeout=120)
        self.invoker_id = invoker_id
        self.target = target
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "Only the host of this roast/toast can press buttons. Run `/roasttoast` yourself.",
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

    def _embed(self, kind: str, line: str) -> Embed:
        if kind == "roast":
            title, color = "🔥 Roast", 0xE65100
        elif kind == "toast":
            title, color = "🥂 Toast", 0xF9A825
        else:
            title, color = "🎲 Surprise", 0x6F4E37
        emb = Embed(title=title, description=line, color=color)
        emb.set_thumbnail(url=self.target.display_avatar.url)
        emb.set_footer(text=f"Target: {self.target.display_name} · Keep it café-playful")
        return emb

    def _line(self, pool: List[str]) -> str:
        return random.choice(pool).format(t=self.target.display_name)

    @discord.ui.button(label="Roast", style=discord.ButtonStyle.danger, emoji="🔥")
    async def roast(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=self._embed("roast", self._line(_ROASTS)), view=self
        )

    @discord.ui.button(label="Toast", style=discord.ButtonStyle.success, emoji="🥂")
    async def toast(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=self._embed("toast", self._line(_TOASTS)), view=self
        )

    @discord.ui.button(label="Surprise", style=discord.ButtonStyle.primary, emoji="🎲")
    async def surprise(self, interaction: discord.Interaction, button: discord.ui.Button):
        kind = random.choice(["roast", "toast"])
        pool = _ROASTS if kind == "roast" else _TOASTS
        await interaction.response.edit_message(
            embed=self._embed("surprise", self._line(pool)), view=self
        )

    @discord.ui.button(label="Another Round", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def another(self, interaction: discord.Interaction, button: discord.ui.Button):
        kind = random.choice(["roast", "toast"])
        pool = _ROASTS if kind == "roast" else _TOASTS
        label = "roast" if kind == "roast" else "toast"
        await interaction.response.edit_message(
            embed=self._embed(label, self._line(pool)), view=self
        )


class Roasttoast(commands.Cog):
    """Café-themed roast or toast with interactive buttons."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.hybrid_command(name="roasttoast")
    async def roasttoast(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Roast or toast someone (or yourself) with café-flavored lines."""
        target = user
        if target is None:
            # Prefer a recent non-bot speaker in the channel, else author
            target = ctx.author
            if ctx.guild and isinstance(ctx.channel, discord.TextChannel):
                candidates = []
                try:
                    async for msg in ctx.channel.history(limit=30):
                        if msg.author.bot or msg.author.id == ctx.author.id:
                            continue
                        if isinstance(msg.author, discord.Member):
                            candidates.append(msg.author)
                except (discord.Forbidden, discord.HTTPException):
                    candidates = []
                if candidates:
                    target = random.choice(candidates)

        if target.bot:
            await ctx.send("Bots don't deserve roasts or toasts. They deserve uptime.")
            return

        view = RoastToastView(ctx.author.id, target)
        opener = Embed(
            title="☕ Roast or Toast?",
            description=(
                f"Target locked: **{target.display_name}**\n"
                "Pick **Roast**, **Toast**, **Surprise**, or **Another Round**."
            ),
            color=0x6F4E37,
        )
        opener.set_thumbnail(url=target.display_avatar.url)
        msg = await ctx.send(embed=opener, view=view)
        view.message = msg
