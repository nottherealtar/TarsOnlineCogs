#
# Chaos Coin — café-flavored coin flips, dice, and oracle answers. No economy, no stakes.
#

from __future__ import annotations

import random
from typing import List, Optional

import discord
from discord import Embed, app_commands
from redbot.core import commands

# --- Outcome pools (add more anytime) ---

_FLIPS: List[str] = [
    "**Heads.** The arabica nods once. That counts as yes.",
    "**Tails.** The grinder has spoken. That's a no with crema.",
    "The coin **vanished into steam**. Interpret that however you dare.",
    "**Heads** — but it landed in someone's **cold brew**. Lukewarm approval.",
    "**Tails.** A sugar packet fell on it. The universe abstains.",
    "It spun forever on the rim of a mug. **Edge case.** Reroll in real life.",
    "**Heads** loud enough to wake the **espresso machine**. Decisive yes.",
    "**Tails.** The foam spelled something rude. Count it as no.",
    "Two beans collided mid-air. **Both sides** won. Chaos wins.",
    "The coin is **decaf**. Nothing matters; flip again if you need drama.",
]

_ASK: List[str] = [
    "The steam says: **yes**, but only after one more sip.",
    "**No.** The French press has judged you.",
    "Ask again when the **milk is steamed** — not before.",
    "**Signs point to** a suspiciously full pastry case.",
    "The oracle is **on break**. Try pretending you didn't ask.",
    "**Absolutely.** The bean spirits are cheering (quietly).",
    "Outlook **hazy** — someone left the lid off the grounds.",
    "**Don't count on it.** Someone used the last filter and didn't replace it.",
    "**Yes**, and you'll tell three people it was your idea.",
    "Reply **unclear**; the barista is experimenting with ratios.",
    "**Very doubtful** — that's a tea drinker's energy.",
    "**Concentrate** — literally. Pull another shot and rethink.",
    "**Without a doubt** — the syrup pump agrees.",
    "**Better not** tell anyone you used this command for that.",
    "Sources say **maybe** if you tip the cosmic scale (metaphorically).",
    "**Outlook good** — the drip finished on time.",
    "**No** — the grinder jammed. That's an omen.",
    "**Yes**, but the foam art will be **abstract**.",
    "Cannot predict now — **someone** is hogging the kettle.",
    "**Most likely** — the beans have spoken in a tasteful whisper.",
    "**Very yes** — suspiciously yes. Check for decaf sabotage.",
    "**Ask your cat** — the coin refuses to engage with this timeline.",
]

_ROLL_OPENERS: List[str] = [
    "The dice clattered into a saucer.",
    "Beans scattered; we counted what mattered.",
    "A ghost barista rolled for you.",
    "The number arrived on latte foam (we transcribed it).",
    "Chaos café math says:",
    "The house blend randomizer returned:",
]


def _roll_verdict(result: int, sides: int) -> str:
    if sides <= 1:
        return "That's not a die, that's a coaster."
    if result == sides:
        return "Natural max — the roast gods are **watching**."
    if result == 1:
        return "Critical low — the grind was too fine today."
    mid = (1 + sides) / 2
    if result >= mid + (sides * 0.25):
        return "High side — bold, possibly reckless, definitely **caffeinated**."
    if result <= mid - (sides * 0.25):
        return "Low roll — subtle, whispery, maybe **under-extracted**."
    return "Middle of the road — balanced, like a boring but **honest** blend."


class Chaoscoin(commands.Cog):
    """Chaos Coin: silly café metaphors for flips, dice, and yes/no asks. No economy."""

    @commands.hybrid_group(name="chaos", invoke_without_command=True)
    async def chaos(self, ctx: commands.Context):
        """Chaos Coin — flip, roll, ask. Pure flavor text."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @chaos.command(name="flip", aliases=["coin"])
    async def chaos_flip(self, ctx: commands.Context):
        """Flip the chaos coin. Not a real coin. Don't bet rent."""
        line = random.choice(_FLIPS)
        embed = Embed(
            title="☕ Chaos coin",
            description=line,
            color=0x6C3483,
        )
        embed.set_footer(text="Not financial advice. Not real probability. Just vibes.")
        await ctx.send(embed=embed)

    @chaos.command(name="roll", aliases=["dice"])
    @app_commands.describe(sides="How many sides (2–100). Default 20.")
    async def chaos_roll(
        self,
        ctx: commands.Context,
        sides: commands.Range[int, 2, 100] = 20,
    ):
        """Roll a die. Number is real; the commentary is artisanal nonsense."""
        result = random.randint(1, sides)
        opener = random.choice(_ROLL_OPENERS)
        verdict = _roll_verdict(result, sides)
        embed = Embed(
            title="🎲 Chaos roll",
            description=f"{opener}\n\n# **{result}** / {sides}\n\n{verdict}",
            color=0x8E44AD,
        )
        embed.set_footer(text="RNG is honest. The prose is not.")
        await ctx.send(embed=embed)

    @chaos.command(name="ask", aliases=["8ball", "oracle"])
    @app_commands.describe(question="Optional question for the cosmic café.")
    async def chaos_ask(self, ctx: commands.Context, *, question: Optional[str] = None):
        """Consult the café oracle. Question optional; judgment is not."""
        answer = random.choice(_ASK)
        embed = Embed(
            title="🔮 Chaos oracle",
            color=0x5B2C6F,
        )
        if question:
            q = question.strip()
            if len(q) > 200:
                q = q[:197] + "…"
            embed.add_field(name="You asked", value=q, inline=False)
        embed.description = answer
        embed.set_footer(text="For entertainment. The real answer is probably water and sleep.")
        await ctx.send(embed=embed)
