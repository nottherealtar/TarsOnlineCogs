#
# Giveaways — button enter, timed end, reroll. MEE6-style.
#

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, List

import discord
from discord import Embed
from redbot.core import Config, commands

log = logging.getLogger("red.nottherealtar.giveaways")


class GiveawayView(discord.ui.View):
    """Persistent enter/leave button; message id comes from the interaction."""

    def __init__(self, cog: "Giveaways"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Enter",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        custom_id="tars_giveaway_enter",
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or interaction.message is None:
            return
        mid = str(interaction.message.id)
        data = await self.cog.config.custom("giveaway", mid).all()
        if not data.get("active"):
            await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
            return
        entrants: List[int] = list(data.get("entrants") or [])
        uid = interaction.user.id
        if uid in entrants:
            entrants.remove(uid)
            await self.cog.config.custom("giveaway", mid).entrants.set(entrants)
            await interaction.response.send_message(
                f"Left the giveaway. ({len(entrants)} entries)", ephemeral=True
            )
        else:
            entrants.append(uid)
            await self.cog.config.custom("giveaway", mid).entrants.set(entrants)
            await interaction.response.send_message(
                f"You're in! ({len(entrants)} entries)", ephemeral=True
            )
        await self.cog._refresh_embed(interaction.message)


class Giveaways(commands.Cog):
    """Create button giveaways with automatic end and reroll."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x61FEA0A1, force_registration=True)
        self.config.init_custom("giveaway", 1)
        self.config.register_custom(
            "giveaway",
            active=False,
            guild_id=None,
            channel_id=None,
            host_id=None,
            prize="",
            winners=1,
            ends_at=0.0,
            entrants=[],
        )
        self._tasks: Dict[int, asyncio.Task] = {}

    async def cog_load(self):
        self.bot.add_view(GiveawayView(self))
        all_g = await self.config.custom("giveaway").all()
        for mid, data in all_g.items():
            if data.get("active"):
                try:
                    self._schedule(int(mid), float(data.get("ends_at") or 0))
                except (TypeError, ValueError):
                    pass

    def cog_unload(self):
        for t in self._tasks.values():
            t.cancel()
        self._tasks.clear()

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        all_g = await self.config.custom("giveaway").all()
        for mid, data in all_g.items():
            entrants = list(data.get("entrants") or [])
            if user_id in entrants:
                await self.config.custom("giveaway", mid).entrants.set(
                    [e for e in entrants if e != user_id]
                )

    def _schedule(self, message_id: int, ends_at: float) -> None:
        old = self._tasks.pop(message_id, None)
        if old:
            old.cancel()
        delay = max(0.0, ends_at - time.time())
        self._tasks[message_id] = asyncio.create_task(self._end_after(message_id, delay))

    async def _end_after(self, message_id: int, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            await self.end_giveaway(message_id)
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("Giveaway end failed for %s", message_id)

    def _build_embed(self, data: dict) -> Embed:
        ends = float(data.get("ends_at") or 0)
        entrants = data.get("entrants") or []
        emb = Embed(
            title="🎉 Giveaway",
            description=f"**Prize:** {data.get('prize') or '—'}\nClick **Enter** to join (again to leave).",
            color=0xE91E63,
        )
        if ends:
            dt = datetime.fromtimestamp(ends, tz=timezone.utc)
            emb.add_field(
                name="Ends",
                value=f"{discord.utils.format_dt(dt, 'R')} ({discord.utils.format_dt(dt, 'f')})",
                inline=False,
            )
        emb.add_field(name="Winners", value=str(data.get("winners") or 1), inline=True)
        emb.add_field(name="Entries", value=str(len(entrants)), inline=True)
        emb.set_footer(text="TarsOnlineCafe giveaways")
        return emb

    async def _refresh_embed(self, message: discord.Message) -> None:
        data = await self.config.custom("giveaway", str(message.id)).all()
        try:
            await message.edit(embed=self._build_embed(data))
        except discord.HTTPException:
            pass

    async def end_giveaway(self, message_id: int, *, forced: bool = False) -> None:
        conf = self.config.custom("giveaway", str(message_id))
        data = await conf.all()
        if not data.get("active") and not forced:
            return
        await conf.active.set(False)
        self._tasks.pop(message_id, None)

        guild = self.bot.get_guild(int(data["guild_id"])) if data.get("guild_id") else None
        if guild is None:
            return
        channel = guild.get_channel(int(data["channel_id"])) if data.get("channel_id") else None
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        entrants = list(data.get("entrants") or [])
        winners_n = max(1, int(data.get("winners") or 1))
        prize = data.get("prize") or "a prize"

        if not entrants:
            emb = Embed(
                title="🎉 Giveaway ended",
                description=f"**{prize}**\nNo valid entries.",
                color=0x95A5A6,
            )
            try:
                await message.edit(embed=emb, view=None)
            except discord.HTTPException:
                pass
            return

        pick = random.sample(entrants, k=min(winners_n, len(entrants)))
        mentions = ", ".join(f"<@{uid}>" for uid in pick)
        emb = Embed(
            title="🎉 Giveaway ended",
            description=f"**{prize}**\n\nWinner(s): {mentions}",
            color=0x2ECC71,
        )
        emb.set_footer(text=f"{len(entrants)} entries · Reroll: giveaway reroll {message_id}")
        try:
            await message.edit(embed=emb, view=None)
            await channel.send(f"Congratulations {mentions}! You won **{prize}**.")
        except discord.HTTPException:
            pass

    @commands.hybrid_group(name="giveaway", aliases=["gway"])
    @commands.guild_only()
    async def giveaway(self, ctx: commands.Context):
        """Create and manage giveaways."""
        if ctx.invoked_subcommand is None:
            emb = Embed(
                title="🎉 Giveaways",
                description=(
                    f"`{ctx.clean_prefix}giveaway start <minutes> [winners] <prize>`\n"
                    f"`{ctx.clean_prefix}giveaway end <message_id>`\n"
                    f"`{ctx.clean_prefix}giveaway reroll <message_id>`"
                ),
                color=0xE91E63,
            )
            await ctx.send(embed=emb)

    @giveaway.command(name="start")
    @commands.admin_or_permissions(manage_guild=True)
    async def giveaway_start(
        self,
        ctx: commands.Context,
        minutes: commands.Range[int, 1, 10080],
        winners: commands.Range[int, 1, 20] = 1,
        *,
        prize: str,
    ):
        """Start a giveaway lasting `minutes` (1–10080)."""
        ends_at = time.time() + minutes * 60
        data = {
            "active": True,
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "host_id": ctx.author.id,
            "prize": prize[:200],
            "winners": winners,
            "ends_at": ends_at,
            "entrants": [],
        }
        msg = await ctx.send(embed=self._build_embed(data), view=GiveawayView(self))
        for k, v in data.items():
            await self.config.custom("giveaway", str(msg.id)).set_raw(k, value=v)
        self._schedule(msg.id, ends_at)

    @giveaway.command(name="end")
    @commands.admin_or_permissions(manage_guild=True)
    async def giveaway_end(self, ctx: commands.Context, message_id: int):
        """End a giveaway early and pick winners."""
        data = await self.config.custom("giveaway", str(message_id)).all()
        if not data.get("guild_id"):
            await ctx.send("No giveaway found with that message ID.")
            return
        await self.end_giveaway(message_id, forced=True)
        await ctx.send("Giveaway ended.", ephemeral=bool(ctx.interaction))

    @giveaway.command(name="reroll")
    @commands.admin_or_permissions(manage_guild=True)
    async def giveaway_reroll(self, ctx: commands.Context, message_id: int):
        """Pick new winner(s) from the original entrants."""
        data = await self.config.custom("giveaway", str(message_id)).all()
        entrants = list(data.get("entrants") or [])
        if not entrants:
            await ctx.send("No entrants to reroll.")
            return
        winners_n = max(1, int(data.get("winners") or 1))
        pick = random.sample(entrants, k=min(winners_n, len(entrants)))
        prize = data.get("prize") or "the prize"
        mentions = ", ".join(f"<@{uid}>" for uid in pick)
        await ctx.send(f"🎲 Reroll for **{prize}**: {mentions}")
