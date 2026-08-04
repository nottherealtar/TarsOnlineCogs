#
# Sticky — keep a message at the bottom of a channel (MEE6-style sticky).
#

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

import discord
from discord import Embed
from redbot.core import Config, commands

log = logging.getLogger("red.nottherealtar.sticky")


class Sticky(commands.Cog):
    """Repost a sticky message after activity so it stays near the bottom."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x571C7001, force_registration=True)
        self.config.register_channel(
            content=None,
            last_message_id=None,
            threshold=4,
            counter=0,
        )
        self._locks: Dict[int, asyncio.Lock] = {}

    async def red_delete_data_for_user(self, **kwargs):
        return

    def _lock(self, channel_id: int) -> asyncio.Lock:
        if channel_id not in self._locks:
            self._locks[channel_id] = asyncio.Lock()
        return self._locks[channel_id]

    async def _repost(self, channel: discord.TextChannel) -> None:
        conf = self.config.channel(channel)
        content = await conf.content()
        if not content:
            return
        async with self._lock(channel.id):
            old_id = await conf.last_message_id()
            if old_id:
                try:
                    old = await channel.fetch_message(old_id)
                    await old.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
            try:
                msg = await channel.send(content[:2000])
            except discord.HTTPException as e:
                log.debug("Sticky send failed in %s: %s", channel.id, e)
                return
            await conf.last_message_id.set(msg.id)
            await conf.counter.set(0)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or not isinstance(message.channel, discord.TextChannel):
            return
        if message.author.id == self.bot.user.id:
            return
        conf = self.config.channel(message.channel)
        content = await conf.content()
        if not content:
            return
        # Ignore our own sticky message id
        if message.id == await conf.last_message_id():
            return
        count = await conf.counter() + 1
        await conf.counter.set(count)
        threshold = max(1, int(await conf.threshold()))
        if count >= threshold:
            await self._repost(message.channel)

    @commands.hybrid_group(name="sticky")
    @commands.guild_only()
    async def sticky(self, ctx: commands.Context):
        """Keep a message stuck near the bottom of a channel."""
        if ctx.invoked_subcommand is None:
            emb = Embed(
                title="📌 Sticky messages",
                description=(
                    f"`{ctx.clean_prefix}sticky set <text>` — set sticky in this channel\n"
                    f"`{ctx.clean_prefix}sticky clear` — remove sticky\n"
                    f"`{ctx.clean_prefix}sticky threshold <n>` — repost after N messages (default 4)\n"
                    f"`{ctx.clean_prefix}sticky show` — show current sticky text"
                ),
                color=0xE67E22,
            )
            await ctx.send(embed=emb)

    @sticky.command(name="set")
    @commands.admin_or_permissions(manage_messages=True)
    async def sticky_set(self, ctx: commands.Context, *, text: str):
        """Set the sticky message for this channel."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send("Stickies only work in text channels.")
            return
        await self.config.channel(ctx.channel).content.set(text[:2000])
        await self.config.channel(ctx.channel).counter.set(0)
        await self._repost(ctx.channel)
        await ctx.send("Sticky set.", delete_after=5)
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, AttributeError):
            pass

    @sticky.command(name="clear")
    @commands.admin_or_permissions(manage_messages=True)
    async def sticky_clear(self, ctx: commands.Context):
        """Remove the sticky from this channel."""
        conf = self.config.channel(ctx.channel)
        old_id = await conf.last_message_id()
        await conf.clear()
        if old_id and isinstance(ctx.channel, discord.TextChannel):
            try:
                msg = await ctx.channel.fetch_message(old_id)
                await msg.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        await ctx.send("Sticky cleared.")

    @sticky.command(name="threshold")
    @commands.admin_or_permissions(manage_messages=True)
    async def sticky_threshold(self, ctx: commands.Context, count: commands.Range[int, 1, 50]):
        """Repost sticky after this many new messages (1–50)."""
        await self.config.channel(ctx.channel).threshold.set(count)
        await ctx.send(f"Sticky threshold set to **{count}** messages.")

    @sticky.command(name="show")
    async def sticky_show(self, ctx: commands.Context):
        """Show the sticky text for this channel."""
        content = await self.config.channel(ctx.channel).content()
        if not content:
            await ctx.send("No sticky in this channel.")
            return
        await ctx.send(embed=Embed(title="Current sticky", description=content[:4000], color=0xE67E22))
