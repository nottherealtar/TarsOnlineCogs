import logging

class Count4U(commands.Cog):
    """Cog for automated counting in the InfiniCount channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"last_count": 0, "counting_channel_name": "infinicount", "interval": 1800}
        self.config.register_guild(**default_guild)
        self.logger = logging.getLogger("red.count4u")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Count4U cog is ready.")
        await self.auto_count()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the counting channel."""
        await self.config.guild(ctx.guild).counting_channel_name.set(channel.name)
        await ctx.send(f"Counting channel has been set to {channel.name}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setinterval(self, ctx, interval: int):
        """Set the counting interval (in seconds)."""
        await self.config.guild(ctx.guild).interval.set(interval)
        await ctx.send(f"Counting interval has been set to {interval} seconds.")
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetcount(self, ctx):
        """Reset the count back to 0."""
        await self.config.guild(ctx.guild).last_count.set(0)
        await ctx.send("Count has been reset to 0.")

    @commands.command()
    async def testcount(self, ctx):
        """Perform a single count operation."""
        try:
            counting_channel_name = await self.config.guild(ctx.guild).counting_channel_name()
            counting_channel = discord.utils.get(ctx.guild.channels, name=counting_channel_name)
            if counting_channel:
                last_count = await self.config.guild(ctx.guild).last_count()
                next_count = last_count + 1
                await counting_channel.send(next_count)
                await self.config.guild(ctx.guild).last_count.set(next_count)
        except Exception as e:
            self.logger.error(f"Error in testcount command: {e}")

    async def auto_count(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                try:
                    counting_channel_name = await self.config.guild(guild).counting_channel_name()
                    counting_channel = discord.utils.get(guild.channels, name=counting_channel_name)
                    if counting_channel:
                        last_count = await self.config.guild(guild).last_count()
                        next_count = last_count + 1
                        await counting_channel.send(next_count)
                        await self.config.guild(guild).last_count.set(next_count)
                except Exception as e:
                    self.logger.error(f"Error in auto_count: {e}")
            interval = await self.config.guild(guild).interval()
            await sleep(interval)  # Count every interval seconds

def setup(bot):
    bot.add_cog(Count4U(bot))