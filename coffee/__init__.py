from .coffee import Coffee

async def setup(bot):
    await bot.add_cog(Coffee(bot))