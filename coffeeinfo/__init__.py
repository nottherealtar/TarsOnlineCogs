from .coffeeinfo import CoffeeInfo

async def setup(bot):
    await bot.add_cog(CoffeeInfo(bot))