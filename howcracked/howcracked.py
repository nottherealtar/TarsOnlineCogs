# howcracked.py
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

        # Get the user to rate
        target_user = user or ctx.author

        # Generate a random cracked percentage
        cracked_percentage = random.uniform(0, 100)

        # Determine the cool power level
        power_level = random.choice(cool_power_levels)

        # Build the embed
        embed = Embed(title=f"How Cracked is {target_user.name}?", color=0x00ff00)
        embed.description = f"{target_user.mention} is {power_level}! {cracked_percentage:.2f}% cracked {random.choice(emojis)}"
        embed.set_footer(text="Powered by the Cracked-o-Meter and goku")

        # Send the embed
        await ctx.send(embed=embed)

# Required to make the cog load
def setup(bot):
    bot.add_cog(HowCracked(bot))