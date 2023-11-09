#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

# coffeeorder.py
from redbot.core import commands
from discord import Embed, User

class Coffee(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coffee(self, ctx, user: User = None):
        """
        Place a coffee order for yourself or someone else.
        """
        # Get the user to order for
        target_user = user or ctx.author

        # Build the coffee-themed embed
        embed = Embed(title=f"Coffee Order for {target_user.name} ☕", color=0x8B4513)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1170989523895865424/1172244571359551498/YourCoffee.gif?ex=655f9cd5&is=654d27d5&hm=cda30beb01cd668d165445ba74c2faed96f595cdef0445d9dca77343a37a2579&")
        embed.set_footer(text="Enjoy your coffee from Tars Online Cafe!")

        # Send the embed
        await ctx.send(embed=embed)
