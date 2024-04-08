from .howgay import HowGay

async def setup(bot):
    await bot.add_cog(HowGay(bot))