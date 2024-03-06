from .count4u import Count4U

async def setup(bot):
    await bot.add_cog(Count4U(bot))