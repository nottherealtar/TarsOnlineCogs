from .varyquote import VaryQuote

async def setup(bot):
    await bot.add_cog(VaryQuote(bot))