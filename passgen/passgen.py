import string
import random
from redbot.core import commands
from discord.ext import commands as ext_commands

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

            # Create the buttons with options for password length
            buttons = [
                Button(style=ButtonStyle.blue, label=str(i), custom_id=f"passgen_length_{i}")
                for i in range(6, 33)
            ]

            # Create a view to handle button interactions
            view = PassgenView(timeout=60)

            # Add the buttons to the view
            for button in buttons:
                view.add_item(button)

            # Send the buttons and view
            await ctx.send("Choose password length:", view=view)

            # Wait for user interaction
            interaction = await view.wait()

            # Get the selected length from the custom_id
            password_length = int(interaction.custom_id.split("_")[-1])

            # Ask for basic or advanced symbols
            await interaction.response.send_message(f"You selected a password length of {password_length}. Now, choose symbol options:")

            # Create the buttons with options for symbol types
            buttons = [
                Button(style=ButtonStyle.green, label="Basic Symbols", custom_id="passgen_basic"),
                Button(style=ButtonStyle.red, label="Advanced Symbols", custom_id="passgen_advanced"),
            ]

            # Create a new view to handle button interactions
            view = PassgenView(timeout=60)

            # Add the buttons to the view
            for button in buttons:
                view.add_item(button)

            # Send the buttons and view
            await interaction.response.edit_message(content="Choose symbol options:", view=view)

            # Wait for user interaction
            interaction = await view.wait()

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
            await interaction.response.delete_message()

        except TimeoutError:
            await ctx.send("Time limit exceeded. Please run the command again.")

        except ValueError:
            await ctx.send("Invalid input. Please run the command again and choose a valid option.")

        except Exception as e:
            # Handle other errors
            await ctx.send(f"An error occurred: {str(e)}")

class PassgenView(ext_commands.View):
    def __init__(self, *, timeout=180):
        super().__Init__(timeout=timeout) # Initializing view with timeout

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True # Disable buttons on timeout

        await self.response.edit(content="Timeout reached. Please run the command again.", view=self) # Edit message on timeout

    async def on_error(self, error, item, interaction):
        for item in self.children:
            item.disabled = True # Disable buttons on error

        await self.response.edit(content=f"An error occurred: {str(error)}", view=self) # Edit message on error
