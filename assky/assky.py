import random
import aiohttp
import discord
from redbot.core import commands
import pyfiglet

class AsSky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @commands.command()
    async def assky(self, ctx, *, text: str):
        if len(text) > 20:
            return await ctx.send("The input text must be less than or equal to 20 characters.")

        font = pyfiglet.DEFAULT_FONT
        result = pyfiglet.figlet_format(text, font=font)
        await ctx.send(f"```\n{result}\n```")