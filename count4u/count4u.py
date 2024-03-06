import discord
from redbot.core import commands, Config, checks
from datetime import datetime, timedelta

class Count4U(commands.Cog):
    """Cog for automated counting."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_guild = {
            "counting_channel_id": None,
            "counting_enabled": False,
            "start_number": 0,
            "last_count_time": None
        }

        self.config.register_guild(**default_guild)

    async def cog_check(self, ctx):
        if not await self.config.guild(ctx.guild).counting_enabled():
            raise commands.CheckFailure("Automated counting is disabled.")
        return True

    @commands.group()
    async def cccount4u(self, ctx):
        """Automated counting commands."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Count4U Subcommands", description="Use these commands to manage automated counting.", color=discord.Color.blue())
            embed.add_field(name="start", value="Set the starting number for automated counting.", inline=False)
            embed.add_field(name="toggle", value="Toggle automated counting.", inline=False)
            embed.add_field(name="channel", value="Set the counting channel for automated counting.", inline=False)
            await ctx.send(embed=embed)

    @cccount4u.command(name="channel")
    @checks.admin_or_permissions(manage_channels=True)
    async def set_counting_channel(self, ctx, channel: discord.TextChannel):
        """Set the counting channel for automated counting."""
        await self.config.guild(ctx.guild).counting_channel_id.set(channel.id)
        await ctx.send(f"Counting channel set to {channel.mention}.")

    @cccount4u.command(name="toggle")
    @checks.admin_or_permissions(manage_channels=True)
    async def toggle_counting(self, ctx, on_off: bool):
        """Toggle automated counting."""
        await self.config.guild(ctx.guild).counting_enabled.set(on_off)
        await ctx.send(f"Automated counting {'enabled' if on_off else 'disabled'}.")

    @cccount4u.command(name="start")
    async def set_start_number(self, ctx, start_number: int):
        """Set the starting number for automated counting."""
        await self.config.guild(ctx.guild).start_number.set(start_number)
        await ctx.send(f"Starting number set to {start_number}.")

    async def start_counting(self, guild):
        counting_channel_id = await self.config.guild(guild).counting_channel_id()
        counting_channel = guild.get_channel(counting_channel_id)
        if counting_channel:
            last_count_time = await self.config.guild(guild).last_count_time()
            if last_count_time is None or datetime.utcnow() - last_count_time >= timedelta(minutes=30):
                start_number = await self.config.guild(guild).start_number()
                await counting_channel.send(f"Starting counting from {start_number}.")
                await self.config.guild(guild).last_count_time.set(datetime.utcnow())
            else:
                async for message in counting_channel.history(limit=1, oldest_first=False):
                    if message.content.isdigit():
                        start_number = int(message.content)
                        await self.config.guild(guild).start_number.set(start_number)
                        await counting_channel.send(f"Starting counting from {start_number}.")
                        return
                start_number = await self.config.guild(guild).start_number()
                await counting_channel.send(f"Starting counting from {start_number}.")

def setup(bot):
    bot.add_cog(Count4U(bot))
