#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

# Import statements 
import discord
import random
import string
from redbot.core import commands

class PassGen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    async def passgen(self, ctx, length: int = None):
        """Generates a random password of the specified length"""

        if length is None:
            await ctx.send("Invalid length. Please enter a password length between 6 and 32.")
            return

        if length < 6 or length > 32:
            await ctx.send("Invalid length. Please enter a password length between 6 and 32.")
            return

        password = self._generate_password(length)

        try:
            embed = discord.Embed(title="Your password:", description=f"`{password}`", color=random.randint(0, 0xFFFFFF))
            await ctx.author.send(embed=embed)
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await ctx.send("Password sent to your DMs!", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM. Please enable DMs from server members and try again.")

    def _generate_password(self, length):
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for i in range(length))