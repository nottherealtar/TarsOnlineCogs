from redbot.core import commands
from discord import Embed
from datetime import datetime

class ProjectPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def projectpost(self, ctx):
        github_thumbnail = "https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png"

        # Function to delete the last N messages from the user
        async def delete_last_n_messages(user, n):
            messages = []
            async for message in ctx.channel.history(limit=n):
                if message.author == user:
                    messages.append(message)
            for message in messages:
                await message.delete()

        # Ask for the user's name
        question1 = await ctx.send("What's your **name**?")
        author_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)
        await delete_last_n_messages(ctx.author, 1)

        # Ask for the project title
        question2 = await ctx.send("What's the **project title**?")
        project_title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)
        await delete_last_n_messages(ctx.author, 1)

        # Ask for the URL to the project
        question3 = await ctx.send("What's the **URL to the project**? (Provide a URL or type 'cancel' to exit)")
        project_url_message = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        if project_url_message.content.lower() == "cancel":
            await delete_last_n_messages(ctx.author, 2)  # Remove the last two questions
            await ctx.send("Project post canceled.")
            return

        if not project_url_message.content.startswith(("http://", "https://")):
            await delete_last_n_messages(ctx.author, 2)  # Remove the last two questions
            await ctx.send("Invalid URL format. Project post canceled.")
            return

        await delete_last_n_messages(ctx.author, 1)

        # Create the timestamp for the current time
        timestamp = datetime.now()

        # Create the nicely formatted embed
        embed = Embed(title=project_title.content, url=project_url_message.content)
        embed.description = f"**Author:** {author_name.content}"
        embed.set_thumbnail(url=github_thumbnail)
        embed.set_footer(text=f"Posted at {timestamp}")

        # Send the nicely formatted embed to the channel
        await ctx.send(embed=embed)
