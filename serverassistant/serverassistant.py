from redbot.core import commands, Config
import discord
import asyncio

class ServerAssistant(commands.Cog):
    """A cog for organizing your Discord server."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group(invoke_without_command=True)
    async def serverassistant(self, ctx):
        """Base command for the ServerAssistant cog."""
        help_message = discord.Embed(
            title="ServerAssistant Commands",
            description="Helpful commands for managing your Discord server.",
            color=0x00ff00
        )
        help_message.add_field(name="[P]serverassistant createcolorroles", value="Create a set of predefined color roles.", inline=False)
        # help_message.add_field(name="[P]serverassistant selectcolorrole", value="Select a color for your role (requires interaction support).", inline=False)
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
            "Cyan": discord.Color.from_rgb(0, 255, 255),
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

        created_roles = []
        skipped_roles = []

        for color_name, color in colors.items():
            if discord.utils.get(ctx.guild.roles, name=color_name):
                skipped_roles.append(color_name)
            else:
                await ctx.guild.create_role(name=color_name, color=color)
                created_roles.append(color_name)

        if created_roles:
            await ctx.send(f"Created roles: {', '.join(created_roles)}")
        if skipped_roles:
            await ctx.send(f"Skipped existing roles: {', '.join(skipped_roles)}")

    # NOTE: selectcolorrole command is commented out as it requires the Star_Utils library
    # Uncomment and install Star_Utils if you want to use this feature
    
    # @serverassistant.command(name="selectcolorrole")
    # async def select_color_role(self, ctx):
    #     """Send an embed with a dropdown for selecting a color role."""
    #     colors = [
    #         "Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Pink", "Teal", "Cyan",
    #         "White", "Black", "Brown", "Gray", "Lime", "Indigo", "Violet", "Gold", "Silver"
    #     ]
    #     await self.paginate_colors(ctx, colors)

    # async def paginate_colors(self, ctx, colors, start_index=0):
    #     """Paginate through color options."""
    #     page_size = 25
    #     end_index = min(start_index + page_size, len(colors))
    #     current_colors = colors[start_index:end_index]

    #     options = [{"label": color} for color in current_colors]

    #     async def color_select_callback(view, interaction, selected_values):
    #         selected_color = selected_values[0]
    #         role = discord.utils.get(ctx.guild.roles, name=selected_color)
    #         if role:
    #             # Remove any existing color roles
    #             for color in colors:
    #                 existing_role = discord.utils.get(ctx.author.roles, name=color)
    #                 if existing_role:
    #                     await ctx.author.remove_roles(existing_role)
    #             # Add the new color role
    #             await ctx.author.add_roles(role)
    #             await interaction.response.send_message(f"You have been given the `{selected_color}` role.", ephemeral=True)
    #         else:
    #             await interaction.response.send_message("Role not found.", ephemeral=True)

    #     view = Dropdown(
    #         options=options,
    #         placeholder="Choose a color role",
    #         function=color_select_callback,
    #         members=[ctx.author.id]
    #     )

    #     if start_index > 0:
    #         view.add_item(discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous"))
    #     if end_index < len(colors):
    #         view.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next"))

    #     message = await ctx.send("Select a color for your role:", view=view)

    #     def check(interaction):
    #         return interaction.user.id == ctx.author.id and interaction.message.id == message.id

    #     try:
    #         interaction = await self.bot.wait_for("interaction", check=check, timeout=60)
    #         if interaction.data["custom_id"] == "next" and end_index < len(colors):
    #             await interaction.response.defer()
    #             await self.paginate_colors(ctx, colors, start_index=end_index)
    #         elif interaction.data["custom_id"] == "previous" and start_index > 0:
    #             await interaction.response.defer()
    #             await self.paginate_colors(ctx, colors, start_index=start_index - page_size)
    #     except asyncio.TimeoutError:
    #         pass

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

        # Split the message if it exceeds Discord's max message length (2000 characters)
        if len(tree_string) > 2000:
            chunks = [tree_string[i:i+1990] for i in range(0, len(tree_string), 1990)]
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")
        else:
            await ctx.send(f"```{tree_string}```")
