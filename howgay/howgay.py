#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User, NotFound
import random

class HowGay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gay_power_levels = {
            "Ultra Mega Super Gay": (90, 100),
            "Super Duper Gay": (80, 90),
            "Mega Gay": (70, 80),
            "Gay": (60, 70),
            "Kinda Gay": (50, 60),
            "Not So Gay": (40, 50),
            "Straight?": (30, 40),
            "Curious": (20, 30),
            "Questioning": (10, 20),
            "Not Gay": (0, 10),
        }
        self.emojis = ["🌈", "💖", "💜", "💙", "💚", "💛", "🧡", "❤️"]

    def determine_power_level(self, percentage):
        for level, (min, max) in self.gay_power_levels.items():
            if min <= percentage < max:
                return level
        return "Not Gay"

    @commands.command()
    async def howgay(self, ctx, user: User = None):
        """
        Rate the gay level of a user or yourself.
        """
        # Get the user to rate
        target_user = user or ctx.author

        # Generate a random gay percentage
        gay_percentage = random.uniform(0, 100)

        # Determine the gay power level based on the percentage
        power_level = self.determine_power_level(gay_percentage)

        # Build the embed
        embed = Embed(title=f"How Gay is {target_user.name}?", color=0x00ff00)
        embed.description = f"{target_user.mention} is {power_level}! {gay_percentage:.2f}% {random.choice(self.emojis)}"
        embed.set_footer(text="Powered by the Gay-o-Meter")

        # Send the embed
        try:
            await ctx.send(embed=embed)
        except NotFound:
            await ctx.send("User not found.")

# Required to make the cog load
def setup(bot):
    bot.add_cog(HowGay(bot))