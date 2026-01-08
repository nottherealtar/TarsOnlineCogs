#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands, checks
from discord import Embed, Member, utils
import asyncio

class VerifyAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def verifyall(self, ctx, member: Member = None):
        # Get the "Verified" role. Change the name if your role is named differently.
        verified_role = utils.get(ctx.guild.roles, name="Verified")
        
        if not verified_role:
            await ctx.send("The 'Verified' role does not exist in this server. Please create it first.")
            return

        if member:
            # If a member is specified, only check that member.
            if len(member.roles) == 1:  # The @everyone role is always assigned, so if a member has 1 role, they have no additional roles.
                await member.add_roles(verified_role)
                await ctx.send(f"{member.name} has been verified.")
            else:
                await ctx.send(f"{member.name} already has roles assigned.")
        else:
            # If no member is specified, check all members.
            total_members = len(ctx.guild.members)
            verified_count = 0
            progress_message = await ctx.send(f"Progress: 0/{total_members} members verified.")
            
            for member in ctx.guild.members:
                if len(member.roles) == 1:  # The @everyone role is always assigned, so if a member has 1 role, they have no additional roles.
                    await member.add_roles(verified_role)
                    verified_count += 1
                    if verified_count % 10 == 0:  # Update progress for every 10 members verified
                        await progress_message.edit(content=f"Progress: {verified_count}/{total_members} members verified.")
                    await asyncio.sleep(1)  # Sleep for 1 second to avoid rate limiting
            
            await progress_message.edit(content=f"All members have been verified. Total verified: {verified_count}/{total_members}")