import discord
from redbot.core import commands, Config
from asyncio import sleep

class Count4U(commands.Cog):
    """Cog for automated counting in the InfiniCount channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"last_count": 0}
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.auto_count()

    async def auto_count(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                counting_channel = discord.utils.get(guild.channels, name="infinicount")
                if counting_channel:
                    last_count = await self.config.guild(guild).last_count()
                    next_count = last_count + 1
                    await counting_channel.send(next_count)
                    await self.config.guild(guild).last_count.set(next_count)
            await sleep(1800)  # Count every 30 minutes

def setup(bot):
    bot.add_cog(Count4U(bot))
