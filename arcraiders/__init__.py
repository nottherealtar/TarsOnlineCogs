from .arcraiders import ArcRaiders


__red_end_user_data_statement__ = "This cog stores guild settings for auto-update channels. No personal user data is stored."


async def setup(bot):
    await bot.add_cog(ArcRaiders(bot))
