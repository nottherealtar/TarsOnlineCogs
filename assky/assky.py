import random
import aiohttp
import discord
from redbot.core import commands
import pyfiglet

class AsSky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fonts = pyfiglet.FigletFont.getFonts()

    @commands.command()
    async def assky(self, ctx, *, text: str):
        if not self.fonts:
            await ctx.send("No fonts found.")
            return

        random_font = random.choice(self.fonts)

        try:
            custom_fig = pyfiglet.Figlet(font=random_font)
            ascii_art = custom_fig.renderText(text)
            await ctx.send("```\n" + ascii_art + "\n```")
        except pyfiglet.FontNotFound:
            await ctx.send("Font not found")