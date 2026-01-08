#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

import requests
import random
import discord
from redbot.core import commands

class TeachMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    async def teachme(self, ctx):
        """
        Retrieves a random Quote from ZenQuotes.io and sends it as an embed.
        """
        url = "https://zenquotes.io/api/random"
        response = requests.get(url)
        data = response.json()
        
        # Check if the data is not empty
        if data:
            quote_data = random.choice(data)
            quote = quote_data["q"]
            author = quote_data["a"]
            
            # Create an embed
            embed = discord.Embed(
                title="Random Quote",
                description=f"❝{quote}❞\n\n❛{author}❜",
                color=0x00FF00  # You can set a different color if desired
            )
            
            # Set the image
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1170989523895865424/1171831428510646374/images-removebg-preview.png?ex=655e1c10&is=654ba710&hm=1d7b63a7050fc22c292c9cc5d243eed848c62afc25c9ba1b00556660ba37714d")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to retrieve a random quote. Please try again later.")
