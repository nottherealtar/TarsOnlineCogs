from .gamedatemate import GameDateMate


__red_end_user_data_statement__ = (
    "This cog stores per-guild Game Date Mate settings only: app base URL, webhook secret, and whether "
    "forwarding is enabled. It does not store message content or chat logs."
)


async def setup(bot):
    await bot.add_cog(GameDateMate(bot))
