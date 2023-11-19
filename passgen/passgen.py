#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

import random
import string
from redbot.core import commands

class PassGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        super().__init__()
        self.cooldown = commands.CooldownMapping.from_cooldown(15, 17, commands.BucketType.user)

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def passgen(self, ctx):
        password = self.generate_password()
        await ctx.author.send(f"Here is your password: ``{password}``")
        await ctx.message.delete()

    def generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for i in range(8))