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

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        is_github_message = await self.bot.wait_for("message", check=check)
        is_github = is_github_message.content.lower()

        if is_github == "yes":
            github_thumbnail = "https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png"
        else:
            github_thumbnail = None

        # Delete the user's input messages and the bot's questions
        await question0.delete()
        await is_github_message.delete()
        await ctx.message.delete()

        # If it's not a GitHub project, proceed with the rest of the questions
        if is_github != "no":
            await ctx.send("Invalid input. Please answer with 'yes' or 'no'.")
            return

        # Ask for the user's name
        question1 = await ctx.send("What's your **name**?")
        author_name = await self.bot.wait_for("message", check=check)

        # Ask for the project title
        question2 = await ctx.send("What's the **project title**?")
        project_title = await self.bot.wait_for("message", check=check)

        # Ask for the URL to the project
        question3 = await ctx.send("What's the **URL to the project**?")
        project_url = await self.bot.wait_for("message", check=check)

        # Create the timestamp for the current time
        timestamp = datetime.now()

        # Create the nicely formatted embed
        embed = Embed(title=project_title.content, url=project_url.content)
        embed.description = f"**Author:** {author_name.content}"
        if github_thumbnail:
            embed.set_thumbnail(url=github_thumbnail)
        embed.set_footer(text=f"Posted at {timestamp}")

        # Delete the user's input messages and the bot's questions
        await question1.delete()
        await question2.delete()
        await question3.delete()
        await ctx.message.delete()

        # Send the nicely formatted embed to the channel
        await ctx.send(embed=embed)
