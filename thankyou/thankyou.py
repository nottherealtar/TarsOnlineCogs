#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

from redbot.core import commands
from discord import Embed, User

class ThankYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    async def thankyou(self, ctx, user: User = None):
        # If no user is mentioned, raise an error
        if not user:
            raise commands.UserFeedbackCheckFailure("Please mention a user to thank.")

        # Image link for the thank you gif
        thank_you_image = "https://cdn.discordapp.com/attachments/1170989523895865424/1172244570709426226/ThankYou.gif?ex=655f9cd4&is=654d27d4&hm=7aea53f0c517c3d78561eca26a36a2856a75f4c7a27f3fb7a0785f309adf296d&"

        # Create the thank you embed
        embed = Embed(title="Thank You!", description=f"Thank you, {user.mention}, for the coffee! ☕", color=0xFFD700)  # Use a suitable color for a coffee theme
        embed.set_image(url=thank_you_image)
        embed.set_footer(text="Enjoy your coffee from Tars Online Cafe!")

        # Send the embed to the specified user
        await ctx.send(embed=embed)

    # Error handling for the case when no user is mentioned
    @thankyou.error
    async def thankyou_error(self, ctx, error):
        if isinstance(error, commands.UserFeedbackCheckFailure):
            await ctx.send(str(error))