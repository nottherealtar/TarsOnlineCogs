#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands
from discord import Embed


class ThankYou(commands.Cog):
    """Send thank you messages to users."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.guild_only()
    async def thankyou(self, ctx, user: discord.Member):
        """
        Send a thank you message to a user.

        Usage: [p]thankyou @user
        """
        if user == ctx.author:
            await ctx.send("You can't thank yourself!")
            return

        if user.bot:
            await ctx.send("You can't thank a bot!")
            return

        thank_you_image = "https://cdn.discordapp.com/attachments/1170989523895865424/1172244570709426226/ThankYou.gif"

        embed = Embed(
            title="Thank You!",
            description=f"{ctx.author.mention} says thank you to {user.mention}!",
            color=0xFFD700
        )
        embed.set_image(url=thank_you_image)
        embed.set_footer(text="Spread the gratitude!")

        await ctx.send(embed=embed)

    @thankyou.error
    async def thankyou_error(self, ctx, error):
        """Handle errors for the thankyou command."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention a user to thank. Usage: `[p]thankyou @user`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Could not find that user. Please mention a valid member.")
