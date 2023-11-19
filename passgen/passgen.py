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
      view = PasswordLengthView(ctx, self.bot)
      await ctx.send("Choose password length:", view=view)
    except Exception as e:
      await ctx.send(f"Error generating password: {e}")


class PasswordLengthView(discord.ui.View):

  def __init__(self, ctx, bot):
    super().__init__()
    self.ctx = ctx
    self.bot = bot

  @discord.ui.button(label="8 Characters")
  async def generate_password_8(self, button, interaction):
    
    length = 8
    password = self._generate_password(length)

    # Handle AttributeError on interaction
    try:
      ctx = await self.bot.get_context(interaction)
    except AttributeError: 
      ctx = None
    
    try:
      await interaction.user.send(f"Here is your password: {password}") 
    except Exception as e:
      if ctx:
        await ctx.send(f"Error sending DM: {e}")

  # Other button methods

  def _generate_password(self, length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))
