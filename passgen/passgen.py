#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

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
        
        view = PasswordLengthView()
        await ctx.send("Choose password length:", view=view)

class PasswordLengthView(discord.ui.View):

    @discord.ui.button(label="8 Characters") 
    async def eight_char(self, button, interaction):
        password = generate_password(8)
        await interaction.response.send_message(f"Here is your 8 character password: ``{password}``")

    @discord.ui.button(label="16 Characters")
    async def sixteen_char(self, button, interaction):
        password = generate_password(16)
        await interaction.response.send_message(f"Here is your 16 character password: ``{password}``")

def generate_password(length):
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choice(chars) for i in range(length))
