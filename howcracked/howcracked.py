#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User
import random

class HowCracked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def howcracked(self, ctx, user: User = None):
        """
        Rate the cracked level of a user or yourself.
        """
        # Define cool power levels and emojis
        cool_power_levels = [
            "Ultra Mega Super Cracked",
            "Super Duper Cracked",
            "Mega Cracked",
            "Cracked",
            "Kinda Cracked",
            "Not So Cracked",
            "Un-Cracked",
            "Butt-Crack-ed",
            "Cement-Crack-ed",
        ]

        emojis = ["💯", "😎", "🔥", "🤯", "👀"]

        cool_ability_levels = [
            "Ultra Mega Super Charismatic",
            "Super Duper Strong",
            "Mega Intelligent",
            "Mildly Psychic",
            "Slightly Telekinetic",
            "Not So Nimble",
            "Un-coordinated",
            "Butt-Smooth Talker",
            "Cement-Brained",
            "Intellect",
            "Rizz",
        ]

        # Get the user to rate
        target_user = user or ctx.author

        # Generate a random cracked percentage
        cracked_percentage = random.uniform(0, 100)

        # Determine the cool power level based on the percentage
        power_level = None
        if cracked_percentage < 7:
            power_level = "Cement-Crack-ed"
        elif cracked_percentage < 25:
            power_level = "Not So Cracked"
        elif cracked_percentage < 50:
            power_level = "Kinda Cracked"
        elif cracked_percentage < 75:
            power_level = "Cracked"
        elif cracked_percentage < 90:
            power_level = "Mega Cracked"
        elif cracked_percentage < 97:
            power_level = "Super Duper Cracked"
        else:
            power_level = "Ultra Mega Super Cracked"

        # Determine the cool ability level based on the percentage
        ability_level = None
        if cracked_percentage < 7:
            ability_level = "Cement-Brained"
        elif cracked_percentage < 25:
            ability_level = "Un-coordinated"
        elif cracked_percentage < 50:
            ability_level = "Not So Nimble"
        elif cracked_percentage < 75:
            ability_level = "Mildly Psychic"
        elif cracked_percentage < 90:
            ability_level = "Slightly Telekinetic"
        elif cracked_percentage < 97:
            ability_level = "Mega Intelligent"
        else:
            ability_level = "Ultra Mega Super Charismatic"

        # Build the embed
        embed = Embed(title=f"How Cracked is {target_user.name}?", color=0x00ff00)
        embed.description = f"{target_user.mention} is {power_level}! {cracked_percentage:.2f}% {ability_level} {random.choice(emojis)}"
        embed.set_footer(text="Powered by the Cracked-o-Meter and goku")

        # Send the embed
        await ctx.send(embed=embed)

# Required to make the cog load
def setup(bot):
    bot.add_cog(HowCracked(bot))