from .verifyall import VerifyAll

async def setup(bot):
    await bot.add_cog(VerifyAll(bot))