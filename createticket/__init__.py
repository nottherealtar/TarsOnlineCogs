from .createticket import CreateTicket

async def setup(bot):
    await bot.add_cog(CreateTicket(bot))