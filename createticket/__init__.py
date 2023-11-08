from .createticket import createticket

async def setup(bot):
    await bot.add_cog(createticket(bot))