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

    @commands.command()
    async def teachme(self, ctx):
        """
        Retrieves a random Quote from ZenQuotes.io.
        """
        url = "https://zenquotes.io/api/random"
        response = requests.get(url)
        data = response.json()
        
        # Check if the data is not empty
        if data:
            quote_data = random.choice(data)
            quote = quote_data["q"]
            author = quote_data["a"]
            await ctx.send(f"``Quote: ❝{quote}❞`` \n``Author: ❛{author}❜``")
        else:
            await ctx.send("Failed to retrieve a random quote. Please try again later.")