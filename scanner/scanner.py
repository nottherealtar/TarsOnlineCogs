#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands, Config


class Scanner(commands.Cog):
    """Scans new members and logs account information for moderation review."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210, force_registration=True)
        default_guild = {
            "auto_scan": False,
            "log_channel_id": None,
            "min_account_age_days": 7  # Flag accounts younger than this
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Scan new members when they join."""
        if member.bot:
            return
        settings = await self.config.guild(member.guild).all()
        if not settings["auto_scan"]:
            return
        if not settings["log_channel_id"]:
            return

        log_channel = member.guild.get_channel(settings["log_channel_id"])
        if not log_channel:
            return

        await self._scan_member(member, log_channel, settings["min_account_age_days"])

    async def _scan_member(self, member, log_channel, min_age_days):
        """Analyze a member and post results to log channel."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        account_age = (now - member.created_at).days
        is_new_account = account_age < min_age_days

        # Build embed
        if is_new_account:
            color = discord.Color.red()
            status = "New Account"
        else:
            color = discord.Color.green()
            status = "Normal"

        embed = discord.Embed(
            title="Member Scan",
            color=color
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M UTC") if member.joined_at else "Unknown", inline=True)

        if is_new_account:
            embed.set_footer(text=f"Account is less than {min_age_days} days old")

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner(self, ctx):
        """Scanner configuration commands."""
        settings = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(settings["log_channel_id"]) if settings["log_channel_id"] else None

        embed = discord.Embed(title="Scanner Settings", color=discord.Color.blue())
        embed.add_field(name="Auto-Scan", value="Enabled" if settings["auto_scan"] else "Disabled", inline=True)
        embed.add_field(name="Log Channel", value=channel.mention if channel else "Not set", inline=True)
        embed.add_field(name="Min Account Age", value=f"{settings['min_account_age_days']} days", inline=True)
        await ctx.send(embed=embed)

    @scanner.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner_enable(self, ctx):
        """Enable auto-scanning of new members."""
        log_channel_id = await self.config.guild(ctx.guild).log_channel_id()
        if not log_channel_id:
            await ctx.send("Please set a log channel first with `scanner channel #channel`.")
            return
        await self.config.guild(ctx.guild).auto_scan.set(True)
        await ctx.send("Auto-scan enabled. New members will be scanned on join.")

    @scanner.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner_disable(self, ctx):
        """Disable auto-scanning of new members."""
        await self.config.guild(ctx.guild).auto_scan.set(False)
        await ctx.send("Auto-scan disabled.")

    @scanner.command(name="channel")
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for scan results."""
        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        await ctx.send(f"Scan results will be posted in {channel.mention}.")

    @scanner.command(name="minage")
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner_minage(self, ctx, days: int):
        """Set minimum account age (in days) before flagging as suspicious."""
        if days < 1 or days > 365:
            await ctx.send("Days must be between 1 and 365.")
            return
        await self.config.guild(ctx.guild).min_account_age_days.set(days)
        await ctx.send(f"Accounts younger than {days} days will be flagged.")

    @scanner.command(name="scan")
    @commands.admin_or_permissions(manage_guild=True)
    async def scanner_scan(self, ctx, member: discord.Member):
        """Manually scan a specific member."""
        settings = await self.config.guild(ctx.guild).all()
        log_channel = ctx.guild.get_channel(settings["log_channel_id"]) if settings["log_channel_id"] else ctx.channel
        await self._scan_member(member, log_channel, settings["min_account_age_days"])
        if log_channel != ctx.channel:
            await ctx.send(f"Scan results posted in {log_channel.mention}.")
