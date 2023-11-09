from .howcracked import HowCracked

async def setup(bot):
    await bot.add_cog(HowCracked(bot))