#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from redbot.core import checks
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import discord
from discord.ext import tasks

class CoffeeInfo(commands.Cog):
    """Cog to display server stats in an automatically updating voice channel style."""

    def __init__(self, bot):
        self.bot = bot
        from redbot.core import Config
        self.config = Config.get_conf(self, identifier=20260108, force_registration=True)
        default_guild = {
            "category_id": None,
            "humans_id": None,
            "bots_id": None,
            "boosts_id": None
        }
        self.config.register_guild(**default_guild)
        self.check_for_updates.start()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group()
    @checks.admin()
    async def coffeeinfo(self, ctx):
        """
        Manage server stats display in voice channels.

        Use `{prefix}coffeeinfo setup` to create stats channels, `{prefix}coffeeinfo update` to refresh, and `{prefix}coffeeinfo revert` to remove them.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @coffeeinfo.command()
    async def setup(self, ctx):
        """
        Create a category and voice channels to display server stats (humans, bots, boosts).

        Use this to set up the stats display for your server.
        """
        try:
            guild = ctx.guild
            # Prevent duplicate category
            category = discord.utils.get(guild.categories, name='☕Server Stats☕')
            if category:
                await ctx.send("A '☕Server Stats☕' category already exists. Use revert first or update.")
                return
            # Check Discord limits
            if len(guild.categories) >= 50:
                await ctx.send("Cannot create category: server has reached the category limit.")
                return
            if len(guild.channels) + 3 > 500:
                await ctx.send("Cannot create channels: server will exceed the channel limit.")
                return
            category = await guild.create_category(name='☕Server Stats☕')
            # Calculate non-bot members
            human_count = sum(1 for member in guild.members if not member.bot)
            bot_count = sum(1 for member in guild.members if member.bot)
            humans_channel = await guild.create_voice_channel(f'Humans: {human_count}', category=category)
            bots_channel = await guild.create_voice_channel(f'Bots: {bot_count}', category=category)
            boosts_channel = await guild.create_voice_channel(f'Server Boosts: {guild.premium_subscription_count}', category=category)
            await self.config.guild(guild).category_id.set(category.id)
            await self.config.guild(guild).humans_id.set(humans_channel.id)
            await self.config.guild(guild).bots_id.set(bots_channel.id)
            await self.config.guild(guild).boosts_id.set(boosts_channel.id)
            await ctx.send("Server stats have been set up in the voice channels under the 'Server Stats' category.")
        except Exception as e:
            await ctx.send(f"An error occurred during setup: {e}")

    @coffeeinfo.command()
    async def revert(self, ctx):
        """
        Remove the server stats display (category and channels) from your server.
        """
        try:
            guild = ctx.guild
            category_id = await self.config.guild(guild).category_id()
            humans_id = await self.config.guild(guild).humans_id()
            bots_id = await self.config.guild(guild).bots_id()
            boosts_id = await self.config.guild(guild).boosts_id()
            # Remove channels if they exist
            for cid in [humans_id, bots_id, boosts_id]:
                channel = guild.get_channel(cid) if cid else None
                if channel:
                    await channel.delete()
            # Remove category if it exists
            category = guild.get_channel(category_id) if category_id else None
            if category and isinstance(category, discord.CategoryChannel):
                await category.delete()
            await self.config.guild(guild).category_id.set(None)
            await self.config.guild(guild).humans_id.set(None)
            await self.config.guild(guild).bots_id.set(None)
            await self.config.guild(guild).boosts_id.set(None)
            await ctx.send("Server stats display has been reverted from the voice channels.")
        except Exception as e:
            await ctx.send(f"An error occurred during revert: {e}")

    @coffeeinfo.command()
    async def update(self, ctx):
        """
        Manually update the counts of humans, bots, and server boosts in the stats channels.
        """
        try:
            guild = ctx.guild
            humans_id = await self.config.guild(guild).humans_id()
            bots_id = await self.config.guild(guild).bots_id()
            boosts_id = await self.config.guild(guild).boosts_id()
            human_count = sum(1 for member in guild.members if not member.bot)
            bot_count = sum(1 for member in guild.members if member.bot)
            if humans_id:
                channel = guild.get_channel(humans_id)
                if channel:
                    await channel.edit(name=f'Humans: {human_count}')
            if bots_id:
                channel = guild.get_channel(bots_id)
                if channel:
                    await channel.edit(name=f'Bots: {bot_count}')
            if boosts_id:
                channel = guild.get_channel(boosts_id)
                if channel:
                    await channel.edit(name=f'Server Boosts: {guild.premium_subscription_count}')
            await ctx.send("Server stats have been manually updated.")
        except Exception as e:
            await ctx.send(f"An error occurred during update: {e}")

    @tasks.loop(seconds=900)
    async def check_for_updates(self):
        for guild in self.bot.guilds:
            humans_id = await self.config.guild(guild).humans_id()
            bots_id = await self.config.guild(guild).bots_id()
            boosts_id = await self.config.guild(guild).boosts_id()
            human_count = sum(1 for member in guild.members if not member.bot)
            bot_count = sum(1 for member in guild.members if member.bot)
            if humans_id:
                channel = guild.get_channel(humans_id)
                if channel:
                    await channel.edit(name=f'Humans: {human_count}')
            if bots_id:
                channel = guild.get_channel(bots_id)
                if channel:
                    await channel.edit(name=f'Bots: {bot_count}')
            if boosts_id:
                channel = guild.get_channel(boosts_id)
                if channel:
                    await channel.edit(name=f'Server Boosts: {guild.premium_subscription_count}')