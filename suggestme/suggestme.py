#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User, utils
from typing import Optional
from datetime import datetime

class SuggestMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_count = 0

    @commands.command()
    async def suggestme(self, ctx, *, suggestion: str):
        """
        Lets members with the Verified role to suggest features for the server and these suggestions get posted in a suggestions channel for the staff to review and for the server to vote for.
        """
        # Check if the user has the Verified role
        verified_role = utils.get(ctx.guild.roles, name="Verified")
        if verified_role is None:
            await ctx.send("The Verified role does not exist.")
            return

        if verified_role in ctx.author.roles:
            # Increment the suggestion count
            self.suggestion_count += 1

            # Get the current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create an embed with the suggestion
            embed = Embed(title=f"Suggestion #{self.suggestion_count} has been added by {ctx.author.name}", description=f'"{suggestion}" - {timestamp}', color=0x800080)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1170989523895865424/1228294937288769567/360_F_528295970_32SSCHm39wg6hufvVjxEpSxAzU5cew29-removebg-preview.png?ex=662b85cd&is=661910cd&hm=c6c99cd66b7510d2806fcc3dcec59c64a3642b5223ebcad45fb54eda903e9117&')

            # Send the suggestion to the context channel
            message = await ctx.send(embed=embed)

            # Add reactions for voting, verifying, and deleting
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            await ctx.send("Your suggestion has been posted.")
        else:
            await ctx.send("You must have the Verified role to suggest features.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Check if the reaction is on a suggestion and the user is a staff member
        staff_role = utils.get(user.guild.roles, name="Staff")
        if staff_role is None:
            await user.send("The Staff role does not exist.")
            return

        if reaction.message.embeds and "Suggestion #" in reaction.message.embeds[0].title and staff_role in user.roles:
            if str(reaction.emoji) == "✅":
                # Get the suggestions channel
                suggestions_channel = utils.get(reaction.message.guild.channels, name="suggestions")
                if suggestions_channel is None:
                    await user.send("The suggestions channel does not exist.")
                    return

                # Publish the suggestion to the suggestions channel
                await suggestions_channel.send(embed=reaction.message.embeds[0])
                await reaction.message.delete()

            elif str(reaction.emoji) == "❌":
                # Delete the suggestion
                await reaction.message.delete()