#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, Member, utils
import asyncio

class VerifyAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def verifyall(self, ctx, member: Member = None):
        # Get the "Verified" role. Change the name if your role is named differently.
        verified_role = utils.get(ctx.guild.roles, name="Verified")

        if member:
            # If a member is specified, only check that member.
            if len(member.roles) == 1:  # The @everyone role is always assigned, so if a member has 1 role, they have no additional roles.
                await member.add_roles(verified_role)
                await ctx.send(f"{member.name} has been verified.")
        else:
            # If no member is specified, check all members.
            total_members = len(ctx.guild.members)
            verified_count = 0
            for member in ctx.guild.members:
                if len(member.roles) == 1:  # The @everyone role is always assigned, so if a member has 1 role, they have no additional roles.
                    await member.add_roles(verified_role)
                    verified_count += 1
                    if verified_count % 10 == 0:  # Update progress for every 10 members verified
                        await ctx.send(f"Progress: {verified_count}/{total_members} members verified.")
                    await asyncio.sleep(3)  # Sleep for 1 second to avoid rate limiting
            await ctx.send("All members have been verified.")