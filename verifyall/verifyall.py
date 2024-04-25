#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User, utils

class VerifyAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def verifyall(self, ctx, user: User = None):
        # Get the "Verified" role. Change the name if your role is named differently.
        verified_role = utils.get(ctx.guild.roles, name="Verified")

        if user:
            # If a user is specified, only check that user.
            if len(user.roles) == 1:  # The @everyone role is always assigned, so if a user has 1 role, they have no additional roles.
                await user.add_roles(verified_role)
                await ctx.send(f"{user.name} has been verified.")
        else:
            # If no user is specified, check all users.
            for member in ctx.guild.members:
                if len(member.roles) == 1:  # The @everyone role is always assigned, so if a user has 1 role, they have no additional roles.
                    await member.add_roles(verified_role)
            await ctx.send("All users have been verified.")