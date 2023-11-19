import string
import random
from redbot.core import commands
from discord.ui import View, Button, ButtonStyle

class Passgen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def passgen(self, ctx):
        """
        Generates a random password based on user input.
        """
        try:
            # Ask for the user's desired password length
            await ctx.send("Please select the desired length for your password:")

            # Button row with options for password length
            buttons = [
                Button(style=ButtonStyle.blue, label=str(i), custom_id=f"passgen_length_{i}")
                for i in range(6, 33)
            ]

            # Send buttons
            message = await ctx.send("Choose password length:", components=buttons)

            # Wait for user interaction
            interaction = await self.bot.wait_for("button_click", check=lambda i: i.custom_id.startswith("passgen_length"), timeout=60)

            # Get the selected length from the custom_id
            password_length = int(interaction.custom_id.split("_")[-1])

            # Ask for basic or advanced symbols
            await interaction.respond(content=f"You selected a password length of {password_length}. Now, choose symbol options:")

            # Button row with options for symbol types
            buttons = [
                Button(style=ButtonStyle.green, label="Basic Symbols", custom_id="passgen_basic"),
                Button(style=ButtonStyle.red, label="Advanced Symbols", custom_id="passgen_advanced"),
            ]

            # Send buttons
            await interaction.edit_origin(content="Choose symbol options:", components=buttons)

            # Wait for user interaction
            interaction = await self.bot.wait_for("button_click", check=lambda i: i.custom_id.startswith("passgen"), timeout=60)

            # Get the selected symbol type from the custom_id
            use_advanced_symbols = "advanced" in interaction.custom_id

            # Generate the password based on user choices
            password_characters = string.ascii_letters + string.digits
            if use_advanced_symbols:
                password_characters += string.punctuation

            generated_password = ''.join(random.choice(password_characters) for _ in range(password_length))
            # Send the generated password via direct message
            await ctx.author.send(f"Here is your generated password: `{generated_password}`")

            # Clean up traces
            await interaction.delete_original_message()
            await message.delete()

        except TimeoutError:
            await ctx.send("Time limit exceeded. Please run the command again.")

        except ValueError:
            await ctx.send("Invalid input. Please run the command again and choose a valid option.")

        except Exception as e:
            # Handle other errors
            await ctx.send(f"An error occurred: {str(e)}")