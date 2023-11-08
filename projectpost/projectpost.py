from redbot.core import commands
from discord import Embed
from datetime import datetime

class ProjectPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def projectpost(self, ctx):
        # Ask for the user's name
        await ctx.send("What's your name?")
        author_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Ask for the project title
        await ctx.send("What's the project title?")
        project_title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Ask for the URL to the project
        await ctx.send("What's the URL to the project?")
        project_url = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Create the timestamp for the current time
        timestamp = datetime.now()

        # Create the embed with the timestamp in the footer
        embed = Embed(title=project_title.content, url=project_url.content, description=f"Author: {author_name.content}")
        embed.set_footer(text=f"Posted at {timestamp}")

        # Send the embed to the channel
        await ctx.send(embed=embed)

        # Delete the user's messages
        await author_name.delete()
        await project_title.delete()
        await project_url.delete()