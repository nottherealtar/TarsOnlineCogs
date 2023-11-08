import requests
import random
import discord
from redbot.core import commands

class TeachMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def teachme(self, ctx):
        url = "https://zenquotes.io/api/random"
        response = requests.get(url)
        data = response.json()
        
        # Check if the data is not empty
        if data:
            quote_data = random.choice(data)
            quote = quote_data["q"]
            author = quote_data["a"]
            await ctx.send(f"``{quote}`` - ``{author}``")
        else:
            await ctx.send("Failed to retrieve a random quote. Please try again later.")