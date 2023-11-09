from .thankyou import ThankYou

async def setup(bot):
    await bot.add_cog(ThankYou(bot))