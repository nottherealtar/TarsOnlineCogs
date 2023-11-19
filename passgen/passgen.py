# passgen.py

import discord
from redbot.core import commands
import random
import string
from discord import ext_command

class PassGen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def passgen(self, ctx):
        """Generates a random password"""
        
        # Create embed
        embed = discord.Embed(title="Password Generator", color=discord.Color.green())
        
        # Add length select menu
        length_select = ["6", "8", "10", "12", "16", "20", "24", "32"] 
        length_menu = discord.ui.Select(placeholder="Select password length", options=[discord.SelectOption(label=i, value=i) for i in length_select])
        length_menu.callback = self.length_callback
        
        # Add symbol select menu
        symbol_select = ["Basic", "Advanced"]
        symbol_menu = discord.ui.Select(placeholder="Select symbol type", options=[discord.SelectOption(label=i, value=i) for i in symbol_select])
        symbol_menu.callback = self.symbol_callback
        
        # Send embed with menus
        view = discord.ui.View()
        view.add_item(length_menu)
        view.add_item(symbol_menu)
        await ctx.send(embed=embed, view=view)

    async def length_callback(self, interaction):
        # Store selected length
        self.length = int(interaction.data['values'][0])
        await interaction.response.defer()

    async def symbol_callback(self, interaction):  
        # Store selected symbols
        self.symbols = interaction.data['values'][0]
        await interaction.response.defer()

        # Generate password
        password = self.generate_password()
        
        # Send password in DM
        await interaction.user.send(f"Here is your generated password: `{password}`")
        
        # Delete original message
        await interaction.message.delete()

    def generate_password(self):
        # Generate password using selected options
        chars = string.ascii_letters + string.digits
        if self.symbols == "Basic":
            chars += "!@#$%^&*()"
        elif self.symbols == "Advanced":
            chars += "!@#$%^&*()_+=-{}[]:;'<>?,./|\\"
            
        password = ''.join(random.choice(chars) for i in range(self.length))
        return password
