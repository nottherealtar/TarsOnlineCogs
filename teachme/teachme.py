#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands
import aiohttp


class TeachMe(commands.Cog):
    """Get random inspirational quotes."""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        """Called when the cog is loaded."""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        if self.session:
            await self.session.close()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def teachme(self, ctx):
        """
        Retrieves a random quote from ZenQuotes.io and sends it as an embed.
        """
        url = "https://zenquotes.io/api/random"

        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    await ctx.send("Failed to retrieve a quote. The service may be unavailable.")
                    return

                data = await response.json()

                if not data or not isinstance(data, list) or len(data) == 0:
                    await ctx.send("Failed to retrieve a quote. Please try again later.")
                    return

                quote_data = data[0]
                quote = quote_data.get("q", "No quote available")
                author = quote_data.get("a", "Unknown")

                embed = discord.Embed(
                    title="Random Quote",
                    description=f"\u275D{quote}\u275E\n\n\u2014 *{author}*",
                    color=0x00FF00
                )

                await ctx.send(embed=embed)

        except aiohttp.ClientError:
            await ctx.send("Failed to connect to the quote service. Please try again later.")
        except Exception as e:
            await ctx.send("An error occurred while fetching your quote.")

    @teachme.error
    async def teachme_error(self, ctx, error):
        """Handle cooldown errors."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Please wait {error.retry_after:.1f} seconds before using this command again.", delete_after=10)
