from .lessonplanner_main import LessonPlannerCog

async def setup(bot):
    await bot.add_cog(LessonPlannerCog(bot))