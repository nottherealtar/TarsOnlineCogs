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

        # Check if the project URL is from GitHub
        is_github = project_url.content.startswith("https://github.com/")

        # Create the embed with or without a thumbnail
        embed = Embed(title=project_title.content, url=project_url.content, description=f"Author: {author_name.content}")
        embed.set_footer(text=f"Posted at {timestamp}")

        # If the URL is from GitHub, add a thumbnail
        if is_github:
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png")

        # Delete the user's input messages and the bot's questions
        await ctx.message.delete()
        await author_name.delete()
        await project_title.delete()
        await project_url.delete()

        # Send the embed to the channel
        await ctx.send(embed=embed)