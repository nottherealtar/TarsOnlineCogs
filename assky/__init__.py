from .assky import assky

async def setup(bot):
    await bot.add_cog(assky(bot))