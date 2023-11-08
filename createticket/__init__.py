from .createticket import createcicket

async def setup(bot):
    await bot.add_cog(createticket(bot))