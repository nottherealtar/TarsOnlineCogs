from .teachme import TeachMe

async def setup(bot):
    await bot.add_cog(TeachMe(bot))