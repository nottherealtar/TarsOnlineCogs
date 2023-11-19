#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

# Import statements 
from redbot.core import commands
import discord
import random
import string

class PassGen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def passgen(self, ctx):
        """Generates a random password of the specified length"""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.author.send("Please enter a password length between 6 and 32.")
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM. Please enter a password length between 6 and 32.")
            return

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('Timeout reached, please run the command again.')
                return

            try:
                length = int(msg.content)
                if length < 6 or length > 32:
                    await ctx.send("Invalid length. Please enter a password length between 6 and 32.")
                    continue
                break
            except ValueError:
                await ctx.send("Invalid input. Please enter a number.")

        password = self._generate_password(length)

        try:
            await ctx.author.send(f"Here is your password: ``{password}``")
            await ctx.send("I have sent you a DM with your password.")
        except discord.Forbidden:
            await ctx.send(f"I couldn't send you a DM. Here is your password: {password}")

    def _generate_password(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))