#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User

class VerifyAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def verifyall(self, ctx, user: User = None):
       #Checks all users and assigns the verified role to users that dont have any roles assigned.
       #Exclude the bot from the list.
       #If a user is specified, only that user will be checked. but if none is specified then it applies to all users.
       