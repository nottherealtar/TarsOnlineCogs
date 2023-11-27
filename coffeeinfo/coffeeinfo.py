import discord
from redbot.core import commands, Config
from discord.ext.commands import has_permissions
from discord.ext import tasks

class CoffeeInfo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12934891293)
        self.config.register_guild(category_id=None)
        self.update_stats.start()

    @tasks.loop(minutes=1)
    async def update_stats(self):
        try:
            guild = self.bot.get_guild(await self.config.guild_id())
            category_id = await self.config.guild(guild).category_id()
            
            if category_id is not None:
                category = guild.get_channel(category_id)
                if category is None:
                    category = await guild.create_category("☕CoffeeInfo☕")
                    await self.config.guild(guild).category_id.set(category.id)
                self.update_channels(category, guild)
        except Exception as error:
            print(f"Error updating stats: {error}")

    def update_channels(self, category, guild):
        channels = category.channels
        
        if len(channels) < 3:
            self.create_stat_channels(category)
            
        for c in channels:
            if c.name.startswith("Humans"):
                c.name = f"Humans: {len(guild.members)}"
            elif c.name.startswith("Bots"):
                c.name = f"Bots: {len([member for member in guild.members if member.bot])}"
            elif c.name.startswith("Server Boosts"):
                c.name = f"Server Boosts: {guild.premium_subscription_count}"

    def create_stat_channels(self, category):
        overwrites = {category.guild.default_role: discord.PermissionOverwrite(connect=False)}
        category.create_voice_channel("Humans", overwrites=overwrites)
        category.create_voice_channel("Bots", overwrites=overwrites)
        category.create_voice_channel("Server Boosts", overwrites=overwrites)

    # Commands
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def coffeeinfo(self, ctx):
        """Manages the CoffeeInfo category and channels"""
        pass
    
    @coffeeinfo.command()
    @has_permissions(administrator=True)
    async def setup(self, ctx):
        """Sets up the CoffeeInfo category and channels"""
        guild = ctx.guild
        category_id = await self.config.guild(guild).category_id()
        if category_id is None:
            category = await guild.create_category("☕CoffeeInfo☕")
            await self.config.guild(guild).category_id.set(category.id)
            self.create_stat_channels(category)
            overwrites = {
        category.guild.default_role: discord.PermissionOverwrite(connect=False)  # Prevents users from connecting
    }
            category.create_voice_channel("Humans", overwrites=overwrites)
            category.create_voice_channel("Bots", overwrites=overwrites)
            category.create_voice_channel("Server Boosts", overwrites=overwrites)
            
            await ctx.send("CoffeeInfo category and channels have been set up.")
        else:
            await ctx.send("CoffeeInfo category and channels already exist.")

    @coffeeinfo.command()
    @has_permissions(administrator=True)
    async def revert(self, ctx):
        """Removes the CoffeeInfo category and channels"""
        category_id = await self.config.guild(ctx.guild).category_id()
        if category_id is not None:
            category = ctx.guild.get_channel(category_id)
            if category:
                for channel in category.channels:
                    await channel.delete()
                await category.delete()
                await self.config.guild(ctx.guild).category_id.clear()
                await ctx.send("CoffeeInfo category and channels have been reverted.")
        else:
            await ctx.send("CoffeeInfo category and channels not found.")

    @setup.error
    @revert.error
    async def setup_revert_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to perform this action.")

    @coffeeinfo.command()
    async def help(self, ctx):
        """Displays this help message"""
        help_text = """
Setup commands:
`[p]coffeeinfo setup`: Sets up the CoffeeInfo category and channels  
`[p]coffeeinfo revert`: Removes the CoffeeInfo category and channels

Management commands:  
`[p]coffeeinfo help`: Displays this help message
        """

        await ctx.send(help_text)