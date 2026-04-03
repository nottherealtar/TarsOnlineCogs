from .serverassistant import ServerAssistant


__red_end_user_data_statement__ = (
    "This cog stores per-guild settings (moderation log, anti-spam, color picker, verification role IDs, "
    "leveling toggles, starboard, reaction-role mappings, role-menu message IDs) and per-member leveling XP only. "
    "It does not store message content or full chat logs."
)


async def setup(bot):
    await bot.add_cog(ServerAssistant(bot))
