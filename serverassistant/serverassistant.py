from redbot.core import commands, Config
import discord
import asyncio

class ServerAssistant(commands.Cog):
        # --- Role Button Verification ---
        @serverassistant.command(name="verifybutton")
        @commands.has_permissions(manage_roles=True)
        async def verifybutton(self, ctx, channel: discord.TextChannel = None, role: discord.Role = None):
            """Send a verification message with a button to assign a role (default: @Verified)."""
            channel = channel or ctx.channel
            if not role:
                # Try to find a role named 'Verified'
                role = discord.utils.get(ctx.guild.roles, name="Verified")
                if not role:
                    await ctx.send("No role specified and no 'Verified' role found.")
                    return
            embed = discord.Embed(title="Verification Required", description=f"Click the button below to verify and get access to the server!\nYou will be given the {role.mention} role.", color=0x43b581)
            view = self._get_verify_view(role.id)
            await channel.send(embed=embed, view=view)
            await ctx.send(f"Verification message sent to {channel.mention}.")

        def _get_verify_view(self, role_id):
            import discord.ui
            from datetime import datetime
            class VerifyView(discord.ui.View):
                def __init__(self, cog, role_id):
                    super().__init__(timeout=None)
                    self.cog = cog
                    self.role_id = role_id

                @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, custom_id="verify_button")
                async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    member = interaction.user
                    role = member.guild.get_role(self.role_id)
                    if not role:
                        await interaction.response.send_message("Role not found.", ephemeral=True)
                        return
                    if role in member.roles:
                        await interaction.response.send_message("You are already verified!", ephemeral=True)
                        return
                    try:
                        await member.add_roles(role, reason="Verified via button")
                        await interaction.response.send_message(f"You have been verified and given the {role.mention} role!", ephemeral=True)
                        # DM the user
                        try:
                            await member.send(f"You have been verified in **{member.guild.name}** at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}! Welcome!")
                        except Exception:
                            pass
                        # Log the verification event
                        log_channel_id = await self.cog.config.guild(member.guild).log_channel()
                        if log_channel_id:
                            log_channel = member.guild.get_channel(log_channel_id)
                            if log_channel:
                                await log_channel.send(f"[Verification] {member.mention} verified at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} in {interaction.channel.mention}.")
                    except Exception as e:
                        await interaction.response.send_message(f"Failed to assign role: {e}", ephemeral=True)

            return VerifyView(self, role_id)
    """A cog for organizing your Discord server."""

    def __init__(self, bot):
        self.bot = bot

        # Config for autorole and logging
        self.config = Config.get_conf(self, identifier=987654321, force_registration=True)
        default_guild = {"autorole": None, "log_channel": None}
        self.config.register_guild(**default_guild)

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
        help_message.add_field(name="[P]serverassistant autorole set @role", value="Set a role to auto-assign to new members.", inline=False)
        help_message.add_field(name="[P]serverassistant announce #channel message", value="Send an announcement to a channel.", inline=False)
        help_message.add_field(name="[P]serverassistant poll 'Question?' 'Option1' 'Option2'", value="Create a poll.", inline=False)
        help_message.add_field(name="[P]serverassistant giveaway #channel duration prize", value="Start a giveaway.", inline=False)
        help_message.add_field(name="[P]serverassistant userinfo @user", value="Show info about a user.", inline=False)
        help_message.add_field(name="[P]serverassistant roleinfo RoleName", value="Show info about a role.", inline=False)
        help_message.add_field(name="[P]serverassistant serverstats", value="Show server statistics.", inline=False)
        help_message.add_field(name="[P]serverassistant kick/ban/mute/unmute/warn/purge", value="Moderation tools.", inline=False)
        help_message.add_field(name="[P]serverassistant log set #channel", value="Set a channel for logging moderation actions.", inline=False)
        await ctx.send(embed=help_message)

    # --- Autorole ---
    @serverassistant.group()
    async def autorole(self, ctx):
        """Auto role assignment settings."""
        pass

    @autorole.command(name="set")
    async def autorole_set(self, ctx, role: discord.Role):
        """Set a role to auto-assign to new members."""
        await self.config.guild(ctx.guild).autorole.set(role.id)
        await ctx.send(f"Autorole set to: {role.mention}")

    @autorole.command(name="show")
    async def autorole_show(self, ctx):
        """Show the current autorole."""
        role_id = await self.config.guild(ctx.guild).autorole()
        role = ctx.guild.get_role(role_id) if role_id else None
        await ctx.send(f"Current autorole: {role.mention if role else 'None'}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = await self.config.guild(member.guild).autorole()
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto role assignment")
                except Exception:
                    pass

    # --- Announce ---
    @serverassistant.command()
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement to a channel."""
        await channel.send(message)
        await ctx.send(f"Announcement sent to {channel.mention}")

    # --- Poll ---
    @serverassistant.command()
    async def poll(self, ctx, question: str, *options):
        """Create a poll. Usage: [p]serverassistant poll 'Question?' 'Option1' 'Option2' ..."""
        if len(options) < 2:
            await ctx.send("You must provide at least two options.")
            return
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        if len(options) > len(emojis):
            await ctx.send(f"Max {len(emojis)} options allowed.")
            return
        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(title=question, description=desc, color=0x3498db)
        poll_msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await poll_msg.add_reaction(emojis[i])

    # --- Giveaway (stub) ---
    @serverassistant.command()
    async def giveaway(self, ctx, channel: discord.TextChannel, duration: str, *, prize: str):
        """Start a giveaway (stub). Usage: [p]serverassistant giveaway #channel 1h Prize"""
        await ctx.send("Giveaway feature coming soon!")

    # --- User Info ---
    @serverassistant.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show info about a user."""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info: {member}", color=member.color)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime('%Y-%m-%d %H:%M'))
        embed.add_field(name="Created", value=member.created_at.strftime('%Y-%m-%d %H:%M'))
        embed.add_field(name="Roles", value=", ".join(r.mention for r in member.roles if r != ctx.guild.default_role))
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- Role Info ---
    @serverassistant.command()
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Show info about a role."""
        embed = discord.Embed(title=f"Role Info: {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Position", value=role.position)
        await ctx.send(embed=embed)

    # --- Server Stats ---
    @serverassistant.command()
    async def serverstats(self, ctx):
        """Show server statistics."""
        guild = ctx.guild
        embed = discord.Embed(title=f"Server Stats: {guild.name}", color=0x7289da)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Humans", value=sum(1 for m in guild.members if not m.bot))
        embed.add_field(name="Bots", value=sum(1 for m in guild.members if m.bot))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        await ctx.send(embed=embed)

    # --- Moderation Tools (stubs) ---

    @serverassistant.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member."""
        try:
            await member.kick(reason=reason or f"Kicked by {ctx.author}")
            await ctx.send(f"{member} has been kicked.")
            await self._log_action(ctx.guild, f"{member} was kicked by {ctx.author}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to kick: {e}")

    @serverassistant.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Ban a member."""
        try:
            await member.ban(reason=reason or f"Banned by {ctx.author}")
            await ctx.send(f"{member} has been banned.")
            await self._log_action(ctx.guild, f"{member} was banned by {ctx.author}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to ban: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """Mute a member (adds Muted role)."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", reason="Mute command used")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        try:
            await member.add_roles(muted_role, reason=reason or f"Muted by {ctx.author}")
            await ctx.send(f"{member} has been muted.")
            await self._log_action(ctx.guild, f"{member} was muted by {ctx.author}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to mute: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member (removes Muted role)."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No Muted role exists.")
            return
        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            await ctx.send(f"{member} has been unmuted.")
            await self._log_action(ctx.guild, f"{member} was unmuted by {ctx.author}.")
        except Exception as e:
            await ctx.send(f"Failed to unmute: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Purge a number of messages."""
        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
            await self._log_action(ctx.guild, f"{ctx.author} purged {len(deleted)} messages in {ctx.channel}.")
        except Exception as e:
            await ctx.send(f"Failed to purge: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """Warn a member (sends DM)."""
        try:
            await member.send(f"You have been warned in {ctx.guild.name}. Reason: {reason or 'No reason provided.'}")
            await ctx.send(f"{member} has been warned.")
            await self._log_action(ctx.guild, f"{member} was warned by {ctx.author}. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"Failed to warn: {e}")

    async def _log_action(self, guild, message):
        log_channel_id = await self.config.guild(guild).log_channel()
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                await channel.send(f"[Moderation Log] {message}")

    # --- Logging (stub) ---
    @serverassistant.group()
    async def log(self, ctx):
        """Logging settings."""
        pass

    @log.command(name="set")
    async def log_set(self, ctx, channel: discord.TextChannel):
        """Set a channel for logging moderation actions."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to: {channel.mention}")

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
