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
import discord


class PassGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

view = discord.ui.View()
chars = ("!@#")

@commands.command()
async def passgen(self, ctx):

    async def eight_char(interaction):
        password = self.generate_password(8)
        await interaction.response.send_message(f"Here is your 8 character password: ``{password}``")

    async def sixteen_char(interaction):
        password = self.generate_password(16) 
        await interaction.response.send_message(f"Here is your 16 character password: ``{password}``")

    eight_button = discord.ui.Button(label="8 Characters", row=1)
    eight_button.callback = eight_char

    sixteen_button = discord.ui.Button(label="16 Characters", row=1)
    sixteen_button.callback = sixteen_char

    view.add_item(eight_button)
    view.add_item(sixteen_button)

    await ctx.send("Choose password length:", view=view)

def generate_password(self, length):
    # Existing password generation code
    return ''.join(random.choice(chars) for i in range(length)) 