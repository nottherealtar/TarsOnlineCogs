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
    async def ccvaryquote(self, ctx):
        """Get a random quote from a chosen category"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @ccvaryquote.command(name="list")
    async def list_categories(self, ctx):
        """
        Display the available quote categories
        """
        categories = ["inspire", "management", "sports", "life", "funny"] 
        embed = discord.Embed(title="Available Categories")
        embed.description = "\n".join(categories)
        await ctx.send(embed=embed)

    @ccvaryquote.command(name="get")
    async def get_quote(self, ctx, category):
        """
        Get a random quote from the specified category
        """
        token = await self.get_api_token()
        url = f"https://api.api-ninjas.com/v1/quotes?category={category}"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                
                if data:
                    quote = random.choice(data)
                    
                    embed = discord.Embed(title=category.capitalize() + " Quote")
                    embed.add_field(name="Quote", value=quote["quote"], inline=False)
                    embed.add_field(name="Author", value=quote["author"], inline=False)
                    
                    await ctx.send(embed=embed)