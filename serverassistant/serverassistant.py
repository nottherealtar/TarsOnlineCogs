from redbot.core import commands, Config
import discord
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class ServerAssistant(commands.Cog):
    """A cog for organizing and protecting your Discord server."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987654321, force_registration=True)
        default_guild = {
            "autorole": None,
            "log_channel": None,
            "antispam_enabled": False,
            "antispam_message_limit": 5,  # messages
            "antispam_time_window": 5,    # seconds
            "antispam_action": "mute",    # mute, kick, or warn
            "antispam_mute_duration": 300 # seconds (5 minutes)
        }
        self.config.register_guild(**default_guild)

        # Anti-spam tracking: {guild_id: {user_id: [timestamps]}}
        self.message_cache = defaultdict(lambda: defaultdict(list))

        # Track persistent views
        self._views_added = False

    async def cog_load(self):
        """Called when the cog is loaded."""
        pass

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
        help_message.add_field(name="[p]serverassistant createcolorroles", value="Create a set of predefined color roles.", inline=False)
        help_message.add_field(name="[p]serverassistant channelmap", value="Generate a mind map of your server's channels.", inline=False)
        help_message.add_field(name="[p]serverassistant autorole set @role", value="Set a role to auto-assign to new members.", inline=False)
        help_message.add_field(name="[p]serverassistant announce #channel message", value="Send an announcement to a channel.", inline=False)
        help_message.add_field(name="[p]serverassistant poll 'Question?' 'Option1' 'Option2'", value="Create a poll.", inline=False)
        help_message.add_field(name="[p]serverassistant userinfo @user", value="Show info about a user.", inline=False)
        help_message.add_field(name="[p]serverassistant roleinfo RoleName", value="Show info about a role.", inline=False)
        help_message.add_field(name="[p]serverassistant serverstats", value="Show server statistics.", inline=False)
        help_message.add_field(name="[p]serverassistant kick/ban/mute/unmute/warn/purge", value="Moderation tools.", inline=False)
        help_message.add_field(name="[p]serverassistant log set #channel", value="Set a channel for logging moderation actions.", inline=False)
        help_message.add_field(name="[p]serverassistant verifybutton", value="Send a verification button message.", inline=False)
        help_message.add_field(name="[p]serverassistant antispam", value="Configure anti-spam protection.", inline=False)
        await ctx.send(embed=help_message)

    # --- Anti-Spam ---
    @serverassistant.group(invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam(self, ctx):
        """Configure anti-spam settings."""
        settings = await self.config.guild(ctx.guild).all()
        embed = discord.Embed(title="Anti-Spam Settings", color=0xff6b6b)
        embed.add_field(name="Enabled", value="Yes" if settings["antispam_enabled"] else "No", inline=True)
        embed.add_field(name="Message Limit", value=str(settings["antispam_message_limit"]), inline=True)
        embed.add_field(name="Time Window", value=f"{settings['antispam_time_window']}s", inline=True)
        embed.add_field(name="Action", value=settings["antispam_action"], inline=True)
        embed.add_field(name="Mute Duration", value=f"{settings['antispam_mute_duration']}s", inline=True)
        embed.set_footer(text="Use subcommands to configure: enable, disable, limit, window, action, mutetime")
        await ctx.send(embed=embed)

    @antispam.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_enable(self, ctx):
        """Enable anti-spam protection."""
        await self.config.guild(ctx.guild).antispam_enabled.set(True)
        await ctx.send("Anti-spam protection enabled.")

    @antispam.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_disable(self, ctx):
        """Disable anti-spam protection."""
        await self.config.guild(ctx.guild).antispam_enabled.set(False)
        await ctx.send("Anti-spam protection disabled.")

    @antispam.command(name="limit")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_limit(self, ctx, limit: int):
        """Set the message limit before triggering anti-spam (default: 5)."""
        if limit < 2 or limit > 20:
            await ctx.send("Limit must be between 2 and 20.")
            return
        await self.config.guild(ctx.guild).antispam_message_limit.set(limit)
        await ctx.send(f"Anti-spam message limit set to {limit}.")

    @antispam.command(name="window")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_window(self, ctx, seconds: int):
        """Set the time window in seconds (default: 5)."""
        if seconds < 2 or seconds > 30:
            await ctx.send("Window must be between 2 and 30 seconds.")
            return
        await self.config.guild(ctx.guild).antispam_time_window.set(seconds)
        await ctx.send(f"Anti-spam time window set to {seconds} seconds.")

    @antispam.command(name="action")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_action(self, ctx, action: str):
        """Set the action when spam is detected: mute, kick, or warn."""
        action = action.lower()
        if action not in ("mute", "kick", "warn"):
            await ctx.send("Action must be `mute`, `kick`, or `warn`.")
            return
        await self.config.guild(ctx.guild).antispam_action.set(action)
        await ctx.send(f"Anti-spam action set to {action}.")

    @antispam.command(name="mutetime")
    @commands.admin_or_permissions(manage_guild=True)
    async def antispam_mutetime(self, ctx, seconds: int):
        """Set mute duration in seconds (default: 300 = 5 minutes)."""
        if seconds < 10 or seconds > 86400:
            await ctx.send("Mute duration must be between 10 and 86400 seconds (24 hours).")
            return
        await self.config.guild(ctx.guild).antispam_mute_duration.set(seconds)
        await ctx.send(f"Anti-spam mute duration set to {seconds} seconds.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for spam."""
        if not message.guild:
            return
        if message.author.bot:
            return
        if not message.author.guild_permissions.send_messages:
            return
        # Skip if user has manage_messages (moderator)
        if message.author.guild_permissions.manage_messages:
            return

        settings = await self.config.guild(message.guild).all()
        if not settings["antispam_enabled"]:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.utcnow()
        time_window = timedelta(seconds=settings["antispam_time_window"])

        # Clean old messages from cache
        self.message_cache[guild_id][user_id] = [
            ts for ts in self.message_cache[guild_id][user_id]
            if now - ts < time_window
        ]

        # Add current message
        self.message_cache[guild_id][user_id].append(now)

        # Check if over limit
        if len(self.message_cache[guild_id][user_id]) >= settings["antispam_message_limit"]:
            # Clear cache to prevent repeat triggers
            self.message_cache[guild_id][user_id] = []
            await self._handle_spam(message, settings)

    async def _handle_spam(self, message, settings):
        """Handle detected spam based on configured action."""
        member = message.author
        action = settings["antispam_action"]
        reason = "Automatic anti-spam action"

        try:
            if action == "mute":
                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted", reason="Anti-spam mute role")
                    for channel in message.guild.channels:
                        try:
                            await channel.set_permissions(muted_role, send_messages=False, speak=False)
                        except discord.Forbidden:
                            pass
                await member.add_roles(muted_role, reason=reason)
                await message.channel.send(f"{member.mention} has been muted for spamming.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was muted for spamming in {message.channel.mention}.")

                # Schedule unmute
                duration = settings["antispam_mute_duration"]
                await asyncio.sleep(duration)
                try:
                    await member.remove_roles(muted_role, reason="Anti-spam mute expired")
                    await self._log_action(message.guild, f"[Anti-Spam] {member} was automatically unmuted after {duration}s.")
                except Exception:
                    pass

            elif action == "kick":
                try:
                    await member.send(f"You have been kicked from **{message.guild.name}** for spamming.")
                except Exception:
                    pass
                await member.kick(reason=reason)
                await message.channel.send(f"{member} has been kicked for spamming.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was kicked for spamming in {message.channel.mention}.")

            elif action == "warn":
                try:
                    await member.send(f"⚠️ Warning: You are sending messages too fast in **{message.guild.name}**. Please slow down.")
                except Exception:
                    pass
                await message.channel.send(f"⚠️ {member.mention}, please slow down! You're sending messages too fast.", delete_after=10)
                await self._log_action(message.guild, f"[Anti-Spam] {member} was warned for spamming in {message.channel.mention}.")

        except discord.Forbidden:
            await self._log_action(message.guild, f"[Anti-Spam] Failed to take action on {member} - missing permissions.")
        except Exception as e:
            await self._log_action(message.guild, f"[Anti-Spam] Error handling spam from {member}: {e}")

    # --- Role Button Verification ---
    @serverassistant.command(name="verifybutton")
    @commands.has_permissions(manage_roles=True)
    async def verifybutton(self, ctx, channel: discord.TextChannel = None, role: discord.Role = None):
        """Send a verification message with a button to assign a role (default: @Verified)."""
        channel = channel or ctx.channel
        if not role:
            role = discord.utils.get(ctx.guild.roles, name="Verified")
            if not role:
                await ctx.send("No role specified and no 'Verified' role found.")
                return
        embed = discord.Embed(
            title="Verification Required",
            description=f"Click the button below to verify and get access to the server!\nYou will be given the {role.mention} role.",
            color=0x43b581
        )
        view = VerifyView(self, role.id)
        await channel.send(embed=embed, view=view)
        await ctx.send(f"Verification message sent to {channel.mention}.")

    # --- Autorole ---
    @serverassistant.group(invoke_without_command=True)
    async def autorole(self, ctx):
        """Auto role assignment settings."""
        role_id = await self.config.guild(ctx.guild).autorole()
        role = ctx.guild.get_role(role_id) if role_id else None
        await ctx.send(f"Current autorole: {role.mention if role else 'None'}")

    @autorole.command(name="set")
    @commands.admin_or_permissions(manage_roles=True)
    async def autorole_set(self, ctx, role: discord.Role):
        """Set a role to auto-assign to new members."""
        await self.config.guild(ctx.guild).autorole.set(role.id)
        await ctx.send(f"Autorole set to: {role.mention}")

    @autorole.command(name="clear")
    @commands.admin_or_permissions(manage_roles=True)
    async def autorole_clear(self, ctx):
        """Clear the autorole setting."""
        await self.config.guild(ctx.guild).autorole.set(None)
        await ctx.send("Autorole has been cleared.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = await self.config.guild(member.guild).autorole()
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto role assignment")
                except discord.Forbidden:
                    pass

    # --- Announce ---
    @serverassistant.command()
    @commands.has_permissions(manage_messages=True)
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

    # --- User Info ---
    @serverassistant.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show info about a user."""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info: {member}", color=member.color)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime('%Y-%m-%d %H:%M') if member.joined_at else "Unknown")
        embed.add_field(name="Created", value=member.created_at.strftime('%Y-%m-%d %H:%M'))
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
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
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    # --- Moderation Tools ---

    @serverassistant.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot kick someone with an equal or higher role.")
            return
        try:
            await member.kick(reason=reason or f"Kicked by {ctx.author}")
            await ctx.send(f"{member} has been kicked.")
            await self._log_action(ctx.guild, f"{member} was kicked by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member.")
        except Exception as e:
            await ctx.send(f"Failed to kick: {e}")

    @serverassistant.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Ban a member."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot ban someone with an equal or higher role.")
            return
        try:
            await member.ban(reason=reason or f"Banned by {ctx.author}")
            await ctx.send(f"{member} has been banned.")
            await self._log_action(ctx.guild, f"{member} was banned by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member.")
        except Exception as e:
            await ctx.send(f"Failed to ban: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """Mute a member (adds Muted role)."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot mute someone with an equal or higher role.")
            return
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", reason="Mute command used")
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
                except discord.Forbidden:
                    pass
        try:
            await member.add_roles(muted_role, reason=reason or f"Muted by {ctx.author}")
            await ctx.send(f"{member} has been muted.")
            await self._log_action(ctx.guild, f"{member} was muted by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this member.")
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
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute this member.")
        except Exception as e:
            await ctx.send(f"Failed to unmute: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Purge a number of messages (max 100)."""
        if amount < 1 or amount > 100:
            await ctx.send("Amount must be between 1 and 100.")
            return
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
            await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)
            await self._log_action(ctx.guild, f"{ctx.author} purged {len(deleted) - 1} messages in {ctx.channel.mention}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except Exception as e:
            await ctx.send(f"Failed to purge: {e}")

    @serverassistant.command()
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """Warn a member (sends DM)."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot warn someone with an equal or higher role.")
            return
        try:
            await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**.\nReason: {reason or 'No reason provided.'}")
            await ctx.send(f"{member} has been warned.")
            await self._log_action(ctx.guild, f"{member} was warned by {ctx.author}. Reason: {reason or 'No reason provided'}")
        except discord.Forbidden:
            await ctx.send(f"{member} has DMs disabled, but the warning has been logged.")
            await self._log_action(ctx.guild, f"{member} was warned by {ctx.author}. Reason: {reason or 'No reason provided'} (DM failed)")

    async def _log_action(self, guild, message):
        log_channel_id = await self.config.guild(guild).log_channel()
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                try:
                    await channel.send(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] {message}")
                except discord.Forbidden:
                    pass

    # --- Logging ---
    @serverassistant.group(invoke_without_command=True)
    async def log(self, ctx):
        """Logging settings."""
        log_channel_id = await self.config.guild(ctx.guild).log_channel()
        channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None
        await ctx.send(f"Current log channel: {channel.mention if channel else 'None'}")

    @log.command(name="set")
    @commands.admin_or_permissions(manage_guild=True)
    async def log_set(self, ctx, channel: discord.TextChannel):
        """Set a channel for logging moderation actions."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to: {channel.mention}")

    @log.command(name="clear")
    @commands.admin_or_permissions(manage_guild=True)
    async def log_clear(self, ctx):
        """Clear the log channel setting."""
        await self.config.guild(ctx.guild).log_channel.set(None)
        await ctx.send("Log channel has been cleared.")

    # --- Color Roles ---
    @serverassistant.command(name="createcolorroles")
    @commands.has_permissions(manage_roles=True)
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
        }

        created_roles = []
        skipped_roles = []

        for color_name, color in colors.items():
            if discord.utils.get(ctx.guild.roles, name=color_name):
                skipped_roles.append(color_name)
            else:
                try:
                    await ctx.guild.create_role(name=color_name, color=color)
                    created_roles.append(color_name)
                except discord.Forbidden:
                    await ctx.send("I don't have permission to create roles.")
                    return

        if created_roles:
            await ctx.send(f"Created roles: {', '.join(created_roles)}")
        if skipped_roles:
            await ctx.send(f"Skipped existing roles: {', '.join(skipped_roles)}")
        if not created_roles and not skipped_roles:
            await ctx.send("No roles to create.")

    # --- Channel Map ---
    @serverassistant.command(name="channelmap")
    async def channel_map(self, ctx):
        """Generate a mind map of the server's channels."""
        channel_list = list(ctx.guild.channels)
        channel_list.sort(key=lambda x: (x.position, str(x.type)))

        tree_string = "Server Channel Structure:\n"
        for channel in channel_list:
            if isinstance(channel, discord.CategoryChannel):
                tree_string += f"📁 {channel.name}\n"
                for sub_channel in sorted(channel.channels, key=lambda x: x.position):
                    if isinstance(sub_channel, discord.TextChannel):
                        tree_string += f"  💬 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.VoiceChannel):
                        tree_string += f"  🔊 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.StageChannel):
                        tree_string += f"  🎭 {sub_channel.name}\n"
                    elif isinstance(sub_channel, discord.ForumChannel):
                        tree_string += f"  📋 {sub_channel.name}\n"
                    else:
                        tree_string += f"  ❓ {sub_channel.name}\n"
            elif channel.category is None:
                if isinstance(channel, discord.TextChannel):
                    tree_string += f"💬 {channel.name}\n"
                elif isinstance(channel, discord.VoiceChannel):
                    tree_string += f"🔊 {channel.name}\n"

        if len(tree_string) > 1990:
            chunks = [tree_string[i:i+1980] for i in range(0, len(tree_string), 1980)]
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")
        else:
            await ctx.send(f"```{tree_string}```")


class VerifyView(discord.ui.View):
    """Persistent verification button view."""

    def __init__(self, cog, role_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.role_id = role_id

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, custom_id="serverassistant_verify")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        role = member.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("Verification role not found. Please contact an admin.", ephemeral=True)
            return
        if role in member.roles:
            await interaction.response.send_message("You are already verified!", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason="Verified via button")
            await interaction.response.send_message(f"You have been verified and given the {role.mention} role!", ephemeral=True)
            # Try to DM the user
            try:
                await member.send(f"You have been verified in **{member.guild.name}**! Welcome!")
            except discord.Forbidden:
                pass
            # Log the verification
            log_channel_id = await self.cog.config.guild(member.guild).log_channel()
            if log_channel_id:
                log_channel = member.guild.get_channel(log_channel_id)
                if log_channel:
                    try:
                        await log_channel.send(f"[Verification] {member.mention} ({member.id}) verified at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.")
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to assign the role. Please contact an admin.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
