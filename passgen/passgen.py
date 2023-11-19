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
        """Generates a random password"""

        try:
            view = PasswordLengthView(ctx)
            await ctx.send("Choose password length:", view=view, delete_after=10)
        except Exception as e:
            await ctx.send(f"Error generating password: {e}")


class PasswordLengthView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Generate Password", style=discord.ButtonStyle.primary)
    async def generate_password(self, button: discord.ui.Button, interaction: discord.Interaction):
        length = random.randint(8, 16)  # Generate a random length between 8 and 16
        password = self._generate_password(length)
        try:
            await interaction.user.send(f"Here is your {length} character password: `{password}`")
        except Exception as e:
            await interaction.response.send_message(f"Error sending DM: {e}", ephemeral=True)

    def _generate_password(self, length):
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(length))
        return password