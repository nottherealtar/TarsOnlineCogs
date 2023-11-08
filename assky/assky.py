import random
import aiohttp
import discord
from redbot.core import commands, app_commands
import os

class AsSky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "http://artii.herokuapp.com/fonts_list"
        self.fonts = []

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url) as response:
                if response.status == 200:
                    data = await response.text()
                    self.fonts = data.split('\n')
                else:
                    print("Error retrieving font list")

    @commands.command()
    async def assky(self, ctx, *, text: str):
        if len(self.fonts) == 0:
            await ctx.send("No fonts found.")
            return

        random_font = random.choice(self.fonts)
        base_url = f"http://artii.herokuapp.com/make?text={text}&font={random_font}"

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    data = await response.text()
                    await ctx.send(f"```\n{data}\n```")
                else:
                    await ctx.send("Error generating ASCII art.")