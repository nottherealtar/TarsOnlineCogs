from redbot.core import commands, Config
import discord
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

COLOR_ROLES = {
    "Warm": {
        "Red": discord.Color.red(),
        "Orange": discord.Color.orange(),
        "Yellow": discord.Color.gold(),
        "Gold": discord.Color.gold(),
        "Pink": discord.Color.magenta(),
    },
    "Cool": {
        "Blue": discord.Color.blue(),
        "Cyan": discord.Color.from_rgb(0, 255, 255),
        "Teal": discord.Color.teal(),
        "Indigo": discord.Color.from_rgb(75, 0, 130),
        "Violet": discord.Color.from_rgb(238, 130, 238),
        "Purple": discord.Color.purple(),
    },
    "Neutral": {
        "White": discord.Color.from_rgb(255, 255, 255),
        "Black": discord.Color.from_rgb(0, 0, 0),
        "Gray": discord.Color.from_rgb(128, 128, 128),
        "Silver": discord.Color.from_rgb(192, 192, 192),
        "Brown": discord.Color.from_rgb(139, 69, 19),
    },
    "Nature": {
        "Green": discord.Color.green(),
        "Lime": discord.Color.from_rgb(191, 255, 0),
    },
}


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
            "antispam_mute_duration": 300, # seconds (5 minutes)
            "colorpicker_channel": None,
            "colorpicker_message": None,
        }
        self.config.register_guild(**default_guild)

        # Anti-spam tracking: {guild_id: {user_id: [timestamps]}}
        self.message_cache = defaultdict(lambda: defaultdict(list))

        # Track persistent views
        self._views_added = False

    async def cog_load(self):
        """Called when the cog is loaded."""
        self.bot.add_view(ColorPickerView(self))

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.hybrid_group(invoke_without_command=True, fallback="help")
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
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
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
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
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
    @app_commands.describe(
        question="The poll question",
        option1="First option (required)",
        option2="Second option (required)",
        option3="Third option",
        option4="Fourth option",
        option5="Fifth option",
        option6="Sixth option",
        option7="Seventh option",
        option8="Eighth option",
        option9="Ninth option",
        option10="Tenth option",
    )
    async def poll(self, ctx, question: str, option1: str, option2: str,
                   option3: str = None, option4: str = None, option5: str = None,
                   option6: str = None, option7: str = None, option8: str = None,
                   option9: str = None, option10: str = None):
        """Create a poll with up to 10 options. Closes automatically after 5 minutes."""
        options = [o for o in [option1, option2, option3, option4, option5,
                                option6, option7, option8, option9, option10] if o]
        view = PollView(question, options)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

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

    # --- Server Owners (Bot Owner Only) ---
    @serverassistant.command(name="owners")
    @commands.is_owner()
    async def server_owners(self, ctx):
        """List all server owners that have the bot. (Bot owner only)"""
        owner_map = {}  # {owner_id: {"user": user_obj, "guilds": [guild_names]}}
        for guild in self.bot.guilds:
            oid = guild.owner_id
            if oid not in owner_map:
                owner_map[oid] = {"user": guild.owner, "guilds": []}
            owner_map[oid]["guilds"].append(guild.name)

        # Sort by server count descending
        sorted_owners = sorted(owner_map.values(), key=lambda x: len(x["guilds"]), reverse=True)

        embeds = []
        per_page = 10
        for page_start in range(0, len(sorted_owners), per_page):
            page_owners = sorted_owners[page_start:page_start + per_page]
            embed = discord.Embed(
                title="Server Owners",
                color=discord.Color.gold(),
            )
            for entry in page_owners:
                user = entry["user"]
                guilds = entry["guilds"]
                name = str(user) if user else f"Unknown User"
                value = f"**Servers ({len(guilds)}):** {', '.join(guilds)}"
                embed.add_field(name=name, value=value, inline=False)

            page_num = page_start // per_page + 1
            total_pages = (len(sorted_owners) + per_page - 1) // per_page
            embed.set_footer(text=f"Page {page_num}/{total_pages} — {len(self.bot.guilds)} total servers")
            embeds.append(embed)

        for embed in embeds:
            await ctx.send(embed=embed, ephemeral=True)

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
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
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
        colors = {}
        for group in COLOR_ROLES.values():
            colors.update(group)

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

    # --- Color Picker ---
    @serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
    @commands.has_permissions(manage_roles=True)
    async def colorpicker(self, ctx):
        """Color picker settings."""
        ch_id = await self.config.guild(ctx.guild).colorpicker_channel()
        channel = ctx.guild.get_channel(ch_id) if ch_id else None
        await ctx.send(f"Color picker channel: {channel.mention if channel else 'Not set up'}")

    @colorpicker.command(name="setup")
    @commands.has_permissions(manage_roles=True)
    async def colorpicker_setup(self, ctx, channel: discord.TextChannel = None):
        """Set up the color role picker. Optionally specify a channel, or one will be created."""
        if channel is None:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    send_messages=False, add_reactions=False
                ),
                ctx.guild.me: discord.PermissionOverwrite(
                    send_messages=True, manage_messages=True
                ),
            }
            channel = await ctx.guild.create_text_channel(
                "color-roles", overwrites=overwrites, reason="Color picker setup"
            )

        embed = discord.Embed(
            title="Choose Your Role Color",
            description=(
                "Pick a color from the dropdowns below to set your name color!\n\n"
                "You can only have **one** color role at a time — "
                "choosing a new one will replace your current color."
            ),
            color=discord.Color.from_rgb(255, 255, 255),
        )
        view = ColorPickerView(self)
        msg = await channel.send(embed=embed, view=view)

        await self.config.guild(ctx.guild).colorpicker_channel.set(channel.id)
        await self.config.guild(ctx.guild).colorpicker_message.set(msg.id)

        await ctx.send(f"Color picker set up in {channel.mention}!")

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


class ColorRoleSelect(discord.ui.Select):
    """A single dropdown for a color group."""

    def __init__(self, cog, group_name, colors):
        options = [
            discord.SelectOption(label=name, value=name)
            for name in colors
        ]
        super().__init__(
            placeholder=f"{group_name} Colors",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"serverassistant_color_{group_name.lower()}",
        )
        self.cog = cog
        self.all_color_names = []
        for group in COLOR_ROLES.values():
            self.all_color_names.extend(group.keys())

    async def callback(self, interaction: discord.Interaction):
        color_name = self.values[0]
        guild = interaction.guild
        member = interaction.user

        # Find the role
        role = discord.utils.get(guild.roles, name=color_name)
        if not role:
            await interaction.response.send_message(
                f"The **{color_name}** role doesn't exist. An admin needs to run `/serverassistant createcolorroles` first.",
                ephemeral=True,
            )
            return

        # Remove existing color roles
        existing_color_roles = [
            r for r in member.roles if r.name in self.all_color_names
        ]
        if existing_color_roles:
            await member.remove_roles(*existing_color_roles, reason="Color role change")

        # Assign new color role
        await member.add_roles(role, reason="Color role selection")
        await interaction.response.send_message(
            f"You've been given the **{color_name}** color role!",
            ephemeral=True,
        )


class ColorPickerView(discord.ui.View):
    """Persistent color picker with grouped dropdowns."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        for group_name, colors in COLOR_ROLES.items():
            self.add_item(ColorRoleSelect(cog, group_name, colors))


class PollButton(discord.ui.Button):
    def __init__(self, label, emoji, option_index):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=emoji,
        )
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        old_vote = view.votes.get(interaction.user.id)
        view.votes[interaction.user.id] = self.option_index

        if old_vote == self.option_index:
            await interaction.response.send_message("You already voted for this!", ephemeral=True)
        elif old_vote is not None:
            await interaction.response.send_message(
                f"Changed your vote to: **{view.options[self.option_index]}**", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"You voted for: **{view.options[self.option_index]}**", ephemeral=True
            )

        # Update embed with new counts
        await interaction.message.edit(embed=view.build_embed())


class PollView(discord.ui.View):
    EMOJIS = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3", "6\u20e3", "7\u20e3", "8\u20e3", "9\u20e3", "\U0001f51f"]

    def __init__(self, question, options):
        super().__init__(timeout=300)  # 5 minutes
        self.question = question
        self.options = options
        self.votes = {}  # {user_id: option_index}
        self.message = None

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, emoji=self.EMOJIS[i], option_index=i))

    def build_embed(self, closed=False):
        counts = {}
        for idx in range(len(self.options)):
            counts[idx] = sum(1 for v in self.votes.values() if v == idx)
        total = sum(counts.values())

        desc_lines = []
        for i, opt in enumerate(self.options):
            count = counts[i]
            pct = f" ({count / total * 100:.0f}%)" if total > 0 else ""
            bar = ""
            if closed and total > 0:
                filled = round(count / total * 10)
                full_block = "\u2588"
                light_block = "\u2591"
                bar = f" {full_block * filled}{light_block * (10 - filled)}"
            desc_lines.append(f"{self.EMOJIS[i]} **{opt}** \u2014 {count} vote{'s' if count != 1 else ''}{pct}{bar}")

        if closed:
            max_votes = max(counts.values())
            if total == 0:
                desc_lines.append("\n**No votes were cast.**")
            else:
                winners = [self.options[i] for i, c in counts.items() if c == max_votes]
                if len(winners) == 1:
                    desc_lines.append(f"\n**Winner: {winners[0]}!**")
                else:
                    desc_lines.append(f"\n**Tie: {', '.join(winners)}!**")

        embed = discord.Embed(
            title=f"{'[CLOSED] ' if closed else ''}\U0001f4ca {self.question}",
            description="\n".join(desc_lines),
            color=discord.Color.red() if closed else discord.Color.blue(),
        )
        if not closed:
            embed.set_footer(text="Poll closes in 5 minutes")
        else:
            embed.set_footer(text=f"Final results \u2014 {total} total vote{'s' if total != 1 else ''}")
        return embed

    async def update_embed(self, message):
        await message.edit(embed=self.build_embed())

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        embed = self.build_embed(closed=True)
        if self.message:
            await self.message.edit(embed=embed, view=self)
