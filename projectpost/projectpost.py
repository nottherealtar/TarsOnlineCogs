#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed
from datetime import datetime

class ProjectPost(commands.Cog):
    """
    Enables the user to create and send an easy embed. eg: is for new release
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def projectpost(self, ctx):
        """
        Enables the user to create and send an easy embed.
        """
        github_thumbnail = "https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png"

        # Function to delete messages
        async def delete_messages(messages):
            for message in messages:
                await message.delete()

        # Ask for the user's name
        question1 = await ctx.send("What's your **name**?")
        author_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)
        messages_to_delete = [question1, author_name]

        # Ask for the project title
        question2 = await ctx.send("What's the **project title**?")
        project_title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)
        messages_to_delete.extend([question2, project_title])

        # Ask for the URL to the project
        question3 = await ctx.send("What's the **URL to the project**? (Provide a URL or type 'cancel' to exit)")
        project_url_message = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)

        if project_url_message.content.lower() == "cancel":
            await delete_messages(messages_to_delete)
            await ctx.send("Project post canceled.")
            await ctx.message.delete()  # Delete the command message
            return

        if not project_url_message.content.startswith(("http://", "https://")):
            await delete_messages(messages_to_delete)
            await ctx.send("Invalid URL format. Project post canceled.")
            await ctx.message.delete()  # Delete the command message
            return

        messages_to_delete.extend([question3, project_url_message])

        # Create the timestamp for the current time
        timestamp = datetime.now()

        # Create the nicely formatted embed
        embed = Embed(title=project_title.content, url=project_url_message.content)
        embed.description = f"**Author:** {author_name.content}"
        embed.set_thumbnail(url=github_thumbnail)
        embed.set_footer(text=f"Posted at {timestamp}")

        # Delete all messages used in the process
        await delete_messages(messages_to_delete)

        # Delete the command message
        await ctx.message.delete()

        # Send the nicely formatted embed to the channel
        await ctx.send(embed=embed)