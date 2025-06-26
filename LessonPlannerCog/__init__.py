from .lessonplannercog import LessonPlannerCog

async def setup(bot):
    await bot.add_cog(LessonPlannerCog(bot))