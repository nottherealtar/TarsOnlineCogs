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
        self.check_for_updates.start()

    @commands.group()
    @checks.admin()
    async def coffeeinfo(self, ctx):
        """Set up server stats in a voice channel to display human, bot, and server boost totals."""
        if ctx.invoked_subcommand is None:
            pass

    @coffeeinfo.command()
    async def setup(self, ctx):
        """Set up the voice channel to display server stats (total humans, bots, and server boosts)."""
        try:
            guild = ctx.guild
            category = await guild.create_category(name='☕Server Stats☕')

            voice_channels = [await guild.create_voice_channel(f'Humans: {guild.member_count}', category=category),
                               await guild.create_voice_channel(f'Bots: {sum(member.bot for member in guild.members)}', category=category),
                               await guild.create_voice_channel(f'Server Boosts: {guild.premium_subscription_count}', category=category)]

            await ctx.send("Server stats have been set up in the voice channels under the 'Server Stats' category.")
        except Exception as e:
            await ctx.send(f"An error occurred during setup: {e}")

    @coffeeinfo.command()
    async def revert(self, ctx):
        """Remove the server stats display from the server."""
        try:
            guild = ctx.guild
            category = discord.utils.get(guild.categories, name='☕Server Stats☕')
            if category:
                for channel in category.voice_channels:
                    await channel.delete()
                await category.delete()
            else:
                await ctx.send("Could not find the '☕Server Stats☕' category. Has the setup been done before?")

            await ctx.send("Server stats display has been reverted from the voice channels.")
        except Exception as e:
            await ctx.send(f"An error occurred during revert: {e}")

    @coffeeinfo.command()
    async def update(self, ctx):
        """Manually update the counts of human, bot, and server boost totals."""
        try:
            guild = ctx.guild
            category = discord.utils.get(guild.categories, name='☕Server Stats☕')
            if category:
                for channel in category.voice_channels:
                    if channel.name.startswith('Humans:'):
                        await channel.edit(name=f'Humans: {guild.member_count}')
                    elif channel.name.startswith('Bots:'):
                        await channel.edit(name=f'Bots: {sum(member.bot for member in guild.members)}')
                    elif channel.name.startswith('Server Boosts:'):
                        await channel.edit(name=f'Server Boosts: {guild.premium_subscription_count}')
                await ctx.send("Server stats have been manually updated.")
            else:
                await ctx.send("Could not find the '☕Server Stats☕' category. Has the setup been done before?")
        except Exception as e:
            await ctx.send(f"An error occurred during update: {e}")

    @tasks.loop(seconds=900)
    async def check_for_updates(self):
        for guild in self.bot.guilds:
            category = discord.utils.get(guild.categories, name='☕Server Stats☕')
            if category:
                for channel in category.voice_channels:
                    if channel.name.startswith('Humans:'):
                        await channel.edit(name=f'Humans: {guild.member_count}')
                    elif channel.name.startswith('Bots:'):
                        await channel.edit(name=f'Bots: {sum(member.bot for member in guild.members)}')
                    elif channel.name.startswith('Server Boosts:'):
                        await channel.edit(name=f'Server Boosts: {guild.premium_subscription_count}')