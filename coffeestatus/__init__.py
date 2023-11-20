from .coffeestatus import CoffeeStatus

async def setup(bot):
    await bot.add_cog(CoffeeStatus(bot))