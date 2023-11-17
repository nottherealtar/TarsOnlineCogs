from .scanner import Scanner

async def setup(bot):
    await bot.add_cog(Scanner(bot))