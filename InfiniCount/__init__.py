from .infinicount import InfiniCount

async def setup(bot):
    await bot.add_cog(InfiniCount(bot))