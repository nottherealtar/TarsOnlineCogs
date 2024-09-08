from redbot.core import commands, Config
import discord
from Star_Utils import Dropdown

class ServerAssistant(commands.Cog):
    """A cog for organizing your Discord server."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def serverassistant(self, ctx):
        """Base command for the ServerAssistant cog."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @serverassistant.command(name="help")
    async def _help(self, ctx):
        """Displays the help diagram for ServerAssistant commands."""
        help_message = discord.Embed(
            title="ServerAssistant Commands",
            description="Helpful commands for managing your Discord server.",
            color=0x00ff00
        )
        help_message.add_field(name="[P]serverassistant createcolorroles", value="Create a set of predefined color roles.", inline=False)
        help_message.add_field(name="[P]serverassistant selectcolorrole", value="Select a color for your role (requires interaction support).", inline=False)
        help_message.add_field(name="[P]serverassistant channelmap", value="Generate a mind map of your server's channels.", inline=False)
        await ctx.send(embed=help_message)

    @serverassistant.command(name="createcolorroles")
    async def create_color_roles(self, ctx):
        """Create a set of predefined color roles."""
        colors = {
            "Red": discord.Color.red(),
            "Green": discord.Color.green(),
            "Blue": discord.Color.blue(),
            "Yellow": discord.Color.gold(),
            "Purple": discord.Color.purple(),
            "Orange": discord.Color.orange(),
            "Pink": discord.Color.magenta(),
            "Teal": discord.Color.teal(),
            "Cyan": discord.Color.cyan(),
            "White": discord.Color.from_rgb(255, 255, 255),
            "Black": discord.Color.from_rgb(0, 0, 0),
            "Brown": discord.Color.from_rgb(139, 69, 19),
            "Gray": discord.Color.from_rgb(128, 128, 128),
            "Lime": discord.Color.from_rgb(191, 255, 0),
            "Indigo": discord.Color.from_rgb(75, 0, 130),
            "Violet": discord.Color.from_rgb(238, 130, 238),
            "Gold": discord.Color.gold(),
            "Silver": discord.Color.from_rgb(192, 192, 192),
            # Add more colors as needed
        }
        for color_name, color in colors.items():
            if discord.utils.get(ctx.guild.roles, name=color_name):
                await ctx.send(f"Role `{color_name}` already exists.")
            else:
                await ctx.guild.create_role(name=color_name, color=color)
                await ctx.send(f"Role `{color_name}` created.")

    @serverassistant.command(name="selectcolorrole")
    async def select_color_role(self, ctx):
        """Send an embed with a dropdown for selecting a color role."""
        colors = [
            "Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Pink", "Teal", "Cyan",
            "White", "Black", "Brown", "Gray", "Lime", "Indigo", "Violet", "Gold", "Silver"
        ]
        options = [discord.SelectOption(label=color) for color in colors]

        async def color_select_callback(view, interaction, selected_values):
            selected_color = selected_values[0]
            role = discord.utils.get(ctx.guild.roles, name=selected_color)
            if role:
                await ctx.author.add_roles(role)
                await interaction.response.send_message(f"You have been given the `{selected_color}` role.", ephemeral=True)
            else:
                await interaction.response.send_message("Role not found.", ephemeral=True)

        view = Dropdown(
            options=options,
            placeholder="Choose a color role",
            function=color_select_callback,
            members=[ctx.author.id]
        )
        await ctx.send("Select a color for your role:", view=view)

    @serverassistant.command(name="channelmap")
    async def channel_map(self, ctx):
        """Generate a mind map of the server's channels."""
        channel_list = list(ctx.guild.channels)  # Convert SequenceProxy to a list
        channel_list.sort(key=lambda x: (x.position, x.type))  # Sort channels by position and type

        tree_string = "Server Channel Structure:\n"
        for channel in channel_list:
            if isinstance(channel, discord.CategoryChannel):
                tree_string += f" {channel.name}\n"
                for sub_channel in channel.channels:
                    tree_string += f"   {sub_channel.name}\n"
            elif isinstance(channel, discord.TextChannel) and channel.category is None:
                tree_string += f" {channel.name}\n"
            elif isinstance(channel, discord.VoiceChannel) and channel.category is None:
                tree_string += f" {channel.name}\n"

        # Ensure the message does not exceed Discord's max message length (2000 characters)
        if len(tree_string) > 2000:
            await ctx.send("The server structure is too large to display in one message. Consider breaking it down.")
        else:
            await ctx.send(f"```{tree_string}```")

def setup(bot):
    bot.add_cog(ServerAssistant(bot))
