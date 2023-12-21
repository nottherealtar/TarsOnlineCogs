import discord
from redbot.core import commands
import aiohttp
import random

BaseCog = getattr(commands, "Cog", object)

class VaryQuote(BaseCog):
    """
    A cog that provides random quotes from various categories
    """

    def __init__(self, bot):
        self.bot = bot
        self.api_token = None

    async def get_api_token(self):
        if not self.api_token:
            token = await self.bot.get_shared_api_tokens("varyquote_api_token")
            self.api_token = token.get("token")
        return self.api_token

    @commands.group()
    async def varyquote(self, ctx):
        """Get a random quote from a chosen category"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @varyquote.command(name="list")
    async def list_categories(self, ctx):
        """
        Display the available quote categories
        """
        categories = ["age", "alone", "amazing", "anger", "architecture", "art", "attitude", "beauty", "best", "birthday", "business", "car", "change", "communication", "computers", "cool", "courage", "dad", "dating", "death", "design", "dreams", "education", "environmental", "equality", "experience", "failure", "faith", "family", "famous", "fear", "fitness"]
        embed = discord.Embed(title="Available Categories") 
        embed.description = "\n".join(categories)
        await ctx.send(embed=embed)

    @varyquote.command(name="get")
    async def get_quote(self, ctx, category):

        """
        Get a random quote from the specified category
        """

        valid_categories = ["age", "alone", "amazing", "anger", "architecture", "art", "attitude", "beauty", "best", "birthday", "business", "car", "change", "communication", "computers", "cool", "courage", "dad", "dating", "death", "design", "dreams", "education", "environmental", "equality", "experience", "failure", "faith", "family", "famous", "fear", "fitness"]

        if category not in valid_categories:
            await ctx.send(f"Invalid category. Use `{ctx.prefix}varyquote list` to view available categories.")
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://varyquote-api.herokuapp.com/quotes/{category}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data: # check if data is not empty
                        quote = random.choice(data)
                        embed = discord.Embed(title=quote["category"], description=quote["quote"])
                        embed.set_footer(text=quote["author"])
                        await ctx.send(embed=embed)
                else:
                    await ctx.send("No quotes are available for the given category.")
                    
