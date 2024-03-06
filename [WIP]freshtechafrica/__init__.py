from .freshtechafrica import FreshTechAfrica

async def setup(bot):
    await bot.add_cog(FreshTechAfrica(bot))