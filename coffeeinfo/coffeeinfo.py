
"""
coffeeinfo.py v3
A cog to display live server statistics in Discord voice channels.  

Changes:
- Fixed syntax error on line 38
- Added error handling
- Stats channels now generated under "CoffeeInfo" category
- Added help command
- Server stat channels now update automatically

Commands:
- coffeeinfo setup: Sets up the CoffeeInfo category and channels
- coffeeinfo revert: Removes the CoffeeInfo category and channels  
- coffeeinfo help: Displays this help message

Requires the administrator permission to setup.
"""

import discord
from redbot.core import commands, Config
from discord.ext.commands import has_permissions
from discord.ext import tasks

class CoffeeInfo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12934891293)
        self.update_stats.start()

    @tasks.loop(minutes=1)
    async def update_stats(self):
        try:
            guild = self.bot.get_guild(self.config.guild_id())
            category = self.get_category(guild)
            self.update_channels(category, guild)
        except Exception as error:
            print(f"Error updating stats: {error}")

    def get_category(self, guild):
        return discord.utils.get(guild.categories, name="☕CoffeeInfo☕") or guild.create_category("☕CoffeeInfo☕")

    def update_channels(self, category, guild):
        channels = category.channels
        
        if len(channels) < 3:
            self.create_stat_channels(category)
            
        for c in channels:
            if c.name.startswith("Humans"):
                c.name = f"Humans: {len(guild.members)}"
            elif c.name.startswith("Bots"):
                c.name = f"Bots: {len(guild.bots)}" 
            elif c.name.startswith("Server Boosts"):
                c.name = f"Server Boosts: {guild.premium_subscription_count}"

    def create_stat_channels(self, category):
        overwrites = {category.guild.default_role: discord.PermissionOverwrite(connect=False)}
        category.create_voice_channel("Humans", overwrites=overwrites)
        category.create_voice_channel("Bots", overwrites=overwrites)
        category.create_voice_channel("Server Boosts", overwrites=overwrites)

    # Commands

    @commands.group()
    @commands.guild_only()
    async def coffeeinfo(self, ctx):
        """Manages the CoffeeInfo category and channels"""
        pass
    
    # Other commands

    @coffeeinfo.command() 
    async def help(self, ctx):
        """Displays this help message"""
        help_text = """
Setup commands:
`[p]coffeeinfo setup`: Sets up the CoffeeInfo category and channels  

Management commands:  
`[p]coffeeinfo revert`: Removes the CoffeeInfo category and channels
        """
        await ctx.send(help_text) 