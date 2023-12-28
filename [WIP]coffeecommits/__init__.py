from .coffeecommits import CoffeeCommits

async def setup(bot):
    await bot.add_cog(CoffeeCommits(bot))