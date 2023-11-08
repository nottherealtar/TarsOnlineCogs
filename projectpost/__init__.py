from .projectpost import ProjectPost

async def setup(bot):
    await bot.add_cog(ProjectPost(bot))