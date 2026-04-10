from .complimentroulette import Complimentroulette


__red_end_user_data_statement__ = "This cog does not persistently store any data or metadata about users."


async def setup(bot):
    await bot.add_cog(Complimentroulette(bot))
