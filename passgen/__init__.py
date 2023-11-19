from .passgen import PassGen

async def setup(bot):
    await bot.add_cog(PassGen(bot))