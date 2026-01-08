import discord
from redbot.core import commands, checks, Config

class InfiniCount(commands.Cog):
    """Cog for creating a counting channel where only +1 increments are allowed."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_guild = {
            "counting_channel_id": None,
            "previous_number": 0
        }

        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group()
    @commands.guild_only()
    async def infinicount(self, ctx):
        """Commands for managing InfiniCount."""
        pass


    async def counting_channel_exists(self, guild):
        counting_channel_id = await self.config.guild(guild).counting_channel_id()
        if counting_channel_id:
            channel = guild.get_channel(counting_channel_id)
            return channel is not None
        return False

    @infinicount.command(name="setup")
    @checks.admin_or_permissions(manage_channels=True)
    async def setup(self, ctx):
        """Setup or reset the InfiniCount channel."""
        guild = ctx.guild
        # Try to find an existing channel
        channel = discord.utils.get(guild.text_channels, name="infinicount")
        if not channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=True),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            channel = await guild.create_text_channel("InfiniCount", overwrites=overwrites)
        await self.config.guild(guild).counting_channel_id.set(channel.id)
        await self.config.guild(guild).previous_number.set(0)
        await self.config.guild(guild).last_counter.set(None)
        await ctx.send(f"InfiniCount channel is set to {channel.mention} and count reset to 0.")

    @infinicount.command(name="set")
    @checks.admin_or_permissions(manage_channels=True)
    async def set_count(self, ctx, number: int):
        """Manually set the current count."""
        await self.config.guild(ctx.guild).previous_number.set(number)
        await ctx.send(f"Count set to {number}.")

    @infinicount.command(name="channel")
    @checks.admin_or_permissions(manage_channels=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the InfiniCount channel."""
        await self.config.guild(ctx.guild).counting_channel_id.set(channel.id)
        await ctx.send(f"InfiniCount channel set to {channel.mention}.")

    @infinicount.command(name="stats")
    async def stats(self, ctx):
        """Show current count and channel."""
        channel_id = await self.config.guild(ctx.guild).counting_channel_id()
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        number = await self.config.guild(ctx.guild).previous_number()
        await ctx.send(f"Current count: {number}\nCounting channel: {channel.mention if channel else 'Not set'}")

    @infinicount.command(name="anticheat")
    @checks.admin_or_permissions(manage_channels=True)
    async def anticheat(self, ctx, enabled: bool):
        """Enable or disable anti-cheat (no double counts in a row)."""
        await self.config.guild(ctx.guild).anticheat.set(enabled)
        await ctx.send(f"Anti-cheat is now {'enabled' if enabled else 'disabled'}.")
    
    @infinicount.command(name="reset")
    @checks.admin_or_permissions(manage_channels=True)
    async def reset_count(self, ctx):
        """Reset the count in the counting channel."""
        guild = ctx.guild
        if await self.counting_channel_exists(guild):
            await self.config.guild(guild).previous_number.set(0)
            await ctx.send("Count has been reset to 0.")
        else:
            await ctx.send("No counting channel exists in this guild.")

    @infinicount.command(name="create")
    @checks.admin_or_permissions(manage_channels=True)
    async def create_counting_channel(self, ctx):
        """Create a counting channel where only +1 increments are allowed."""
        guild = ctx.guild
        if await self.counting_channel_exists(guild):
            return await ctx.send("A counting channel already exists in this guild.")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            guild.me: discord.PermissionOverwrite(send_messages=True)
        }

        counting_channel = await guild.create_text_channel("InfiniCount", overwrites=overwrites)
        await self.config.guild(guild).counting_channel_id.set(counting_channel.id)
        await ctx.send("Counting channel created successfully.")


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        counting_channel_id = await self.config.guild(message.guild).counting_channel_id()
        if not counting_channel_id:
            return
        channel = message.guild.get_channel(counting_channel_id)
        if not channel or channel.id != message.channel.id:
            return

        content = message.content.strip()
        if not content.isdigit():
            await message.delete()
            try:
                await message.author.send(f"Your message in {channel.mention} was deleted: only numbers are allowed.")
            except Exception:
                pass
            return

        number = int(content)
        previous_number = await self.config.guild(message.guild).previous_number()
        anticheat = await self.config.guild(message.guild).anticheat() if await self.config.guild(message.guild).exists() and hasattr(self.config.guild(message.guild), 'anticheat') else False
        last_counter = await self.config.guild(message.guild).last_counter() if await self.config.guild(message.guild).exists() and hasattr(self.config.guild(message.guild), 'last_counter') else None

        # Anti-cheat: prevent same user from counting twice in a row
        if anticheat and last_counter == message.author.id:
            await message.delete()
            try:
                await message.author.send(f"You cannot count twice in a row in {channel.mention}.")
            except Exception:
                pass
            return

        if number != (previous_number + 1):
            await message.delete()
            try:
                await message.author.send(f"Your message in {channel.mention} was deleted: only the next number ({previous_number + 1}) is allowed.")
            except Exception:
                pass
            return

        await self.config.guild(message.guild).previous_number.set(number)
        await self.config.guild(message.guild).last_counter.set(message.author.id)
        try:
            await message.add_reaction("✅")
        except Exception:
            pass
