from .serverassistnat import ServerAssistant

async def setup(bot):
    await bot.add_cog(ServerAssistant(bot))