from .cooldownbuddy import CooldownBuddy


__red_end_user_data_statement__ = (
    "Stores per-guild per-member BRB end time (Unix timestamp) and the channel ID where BRB was set, "
    "for timer announcements and ping deflection. Stores guild timezone name (IANA) for `at`/`until` parsing."
)


async def setup(bot):
    await bot.add_cog(CooldownBuddy(bot))
