from .prompt import TVideo

async def setup(bot):
    await bot.add_cog(TVideo(bot))