#
# PassGen — interactive password generator (discord.ui Select + Buttons).
# Also supports legacy `[p]passgen <length>` for existing muscle memory.
#

from __future__ import annotations

import random
import string
from typing import Optional

import discord
from discord import app_commands
from redbot.core import commands


def _generate(length: int, *, advanced: bool) -> str:
    chars = string.ascii_letters + string.digits
    if advanced:
        chars += string.punctuation
    return "".join(random.choice(chars) for _ in range(length))


class PassGenView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=90)
        self.owner_id = owner_id
        self.length: Optional[int] = None
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This password generator isn't yours. Run the command yourself.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="Password generator timed out.", view=self)
            except (discord.HTTPException, discord.NotFound):
                pass

    @discord.ui.select(
        placeholder="Choose password length…",
        options=[
            discord.SelectOption(label=f"{n} characters", value=str(n))
            for n in (8, 12, 16, 20, 24, 28, 32)
        ],
    )
    async def length_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.length = int(select.values[0])
        await interaction.response.edit_message(
            content=f"Length **{self.length}**. Now choose symbol style:",
            view=self,
        )

    @discord.ui.button(label="Basic (letters + digits)", style=discord.ButtonStyle.primary)
    async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, advanced=False)

    @discord.ui.button(label="Advanced (+ punctuation)", style=discord.ButtonStyle.danger)
    async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, advanced=True)

    async def _finish(self, interaction: discord.Interaction, *, advanced: bool) -> None:
        if self.length is None:
            await interaction.response.send_message(
                "Pick a length from the dropdown first.", ephemeral=True
            )
            return

        password = _generate(self.length, advanced=advanced)
        for item in self.children:
            item.disabled = True

        try:
            embed = discord.Embed(
                title="Your password",
                description=f"`{password}`",
                color=discord.Color.blurple(),
            )
            embed.set_footer(text="Store it somewhere safe — this message won't be repeated here.")
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.edit_message(
                content=(
                    "I couldn't DM you. Enable DMs from server members, then run the command again."
                ),
                view=self,
            )
            self.stop()
            return

        await interaction.response.edit_message(
            content="Password sent to your DMs. This channel keeps no copy.",
            view=self,
        )
        self.stop()


class PassGen(commands.Cog):
    """Generate a secure password via interactive UI (or quick length arg) and receive it in DMs."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def _dm_password(self, ctx: commands.Context, password: str) -> None:
        try:
            embed = discord.Embed(
                title="Your password",
                description=f"`{password}`",
                color=discord.Color.blurple(),
            )
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(
                "I couldn't DM you. Enable DMs from server members and try again.",
                ephemeral=bool(ctx.interaction),
            )
            return

        notice = "Password sent to your DMs!"
        if ctx.interaction:
            await ctx.send(notice, ephemeral=True)
        else:
            await ctx.send(notice, delete_after=5)
            if ctx.message:
                try:
                    await ctx.message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

    @commands.hybrid_command(name="passgen")
    @app_commands.describe(
        length="Optional quick length 6–32 (skips the menu). Leave empty for the button UI."
    )
    async def passgen(self, ctx: commands.Context, length: Optional[int] = None):
        """Generate a password. Omit length for the interactive menu; or pass 6–32 for a quick DM."""
        if length is not None:
            if length < 6 or length > 32:
                await ctx.send("Length must be between **6** and **32**.")
                return
            password = _generate(length, advanced=True)
            await self._dm_password(ctx, password)
            return

        view = PassGenView(ctx.author.id)
        msg = await ctx.send(
            "Choose a password length, then Basic or Advanced symbols:",
            view=view,
        )
        view.message = msg
