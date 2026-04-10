from .coffee import Coffee


__red_end_user_data_statement__ = (
    "Stores per-guild per-member coffee check-in data: last check-in date (UTC), current streak, "
    "best streak, and total check-in count. Used for titles and leaderboards."
)


async def setup(bot):
    await bot.add_cog(Coffee(bot))
