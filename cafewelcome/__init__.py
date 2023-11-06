from .cafewelcome import CafeWelcome


async def setup(bot):
    await bot.add_cog(CafeWelcome(bot))