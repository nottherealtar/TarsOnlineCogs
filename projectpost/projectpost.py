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
from datetime import datetime
import asyncio


class ProjectPost(commands.Cog):
    """Enables the user to create and send an easy embed for project releases."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.guild_only()
    async def projectpost(self, ctx):
        """
        Interactively create and send a project announcement embed.
        """
        github_thumbnail = "https://cdn.discordapp.com/attachments/1170989523895865424/1171787440583872512/Github.png"
        timeout = 120  # 2 minutes

        messages_to_delete = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Ask for the user's name
            question1 = await ctx.send("What's your **name**? (Type 'cancel' to exit)")
            messages_to_delete.append(question1)
            author_name = await self.bot.wait_for("message", check=check, timeout=timeout)
            messages_to_delete.append(author_name)

            if author_name.content.lower() == "cancel":
                await self._cleanup(messages_to_delete, ctx)
                await ctx.send("Project post canceled.", delete_after=10)
                return

            # Ask for the project title
            question2 = await ctx.send("What's the **project title**?")
            messages_to_delete.append(question2)
            project_title = await self.bot.wait_for("message", check=check, timeout=timeout)
            messages_to_delete.append(project_title)

            if project_title.content.lower() == "cancel":
                await self._cleanup(messages_to_delete, ctx)
                await ctx.send("Project post canceled.", delete_after=10)
                return

            # Ask for the URL to the project
            question3 = await ctx.send("What's the **URL to the project**? (Must start with http:// or https://)")
            messages_to_delete.append(question3)
            project_url_message = await self.bot.wait_for("message", check=check, timeout=timeout)
            messages_to_delete.append(project_url_message)

            if project_url_message.content.lower() == "cancel":
                await self._cleanup(messages_to_delete, ctx)
                await ctx.send("Project post canceled.", delete_after=10)
                return

            if not project_url_message.content.startswith(("http://", "https://")):
                await self._cleanup(messages_to_delete, ctx)
                await ctx.send("Invalid URL format. Project post canceled.", delete_after=10)
                return

            # Create the timestamp
            timestamp = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

            # Create the embed
            embed = Embed(title=project_title.content, url=project_url_message.content, color=0x2b2d31)
            embed.description = f"**Author:** {author_name.content}"
            embed.set_thumbnail(url=github_thumbnail)
            embed.set_footer(text=f"Posted at {timestamp}")

            # Cleanup and send
            await self._cleanup(messages_to_delete, ctx)
            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await self._cleanup(messages_to_delete, ctx)
            await ctx.send("Project post timed out. Please try again.", delete_after=10)

    async def _cleanup(self, messages, ctx):
        """Delete messages used in the process."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        for message in messages:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
