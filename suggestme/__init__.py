from .suggestme import SuggestMe

async def setup(bot):
    await bot.add_cog(SuggestMe(bot))