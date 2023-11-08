from redbot.core import commands
from discord import Embed
from datetime import datetime

class ProjectPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def projectpost(self, ctx):
        # Ask if it's a GitHub project
        question0 = await ctx.send("Is it a GitHub project? (yes/no)")
        is_github = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        if is_github.content.lower() == "yes":
            github_thumbnail = "https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png"
        else:
            github_thumbnail = None

        # Ask for the user's name
        question1 = await ctx.send("What's your **name**?")
        author_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Ask for the project title
        question2 = await ctx.send("What's the **project title**?")
        project_title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Ask for the URL to the project
        question3 = await ctx.send("What's the **URL to the project**?")
        project_url = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        # Create the timestamp for the current time
        timestamp = datetime.now()

        # Create the nicely formatted embed
        embed = Embed(title=project_title.content, url=project_url.content)
        embed.description = f"**Author:** {author_name.content}"
        if github_thumbnail:
            embed.set_thumbnail(url=github_thumbnail)
        embed.set_footer(text=f"Posted at {timestamp}")

        # Delete the user's input messages and the bot's questions
        await question0.delete()
        await question1.delete()
        await question2.delete()
        await question3.delete()
        await ctx.message.delete()

        # Send the nicely formatted embed to the channel
        await ctx.send(embed=embed)