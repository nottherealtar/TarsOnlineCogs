import discord
from redbot.core import commands, checks, Config
import random

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

    @commands.group()
    @commands.guild_only()
    async def infinicount(self, ctx):
        """Commands for managing InfiniCount."""
        pass

    @infinicount.command(name="create")
    @checks.admin_or_permissions(manage_channels=True)
    async def create_counting_channel(self, ctx):
        """Create a counting channel where only +1 increments are allowed."""
        guild = ctx.guild
        counting_channel_id = await self.config.guild(guild).counting_channel_id()

        if counting_channel_id:
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
        if not message.guild:
            return

        counting_channel_id = await self.config.guild(message.guild).counting_channel_id()

        if counting_channel_id == message.channel.id:
            content = message.content
            if not content.isdigit() or int(content) != (await self.config.guild(message.guild).previous_number() + 1):
                await message.delete()
                await message.channel.send("Invalid number! Only +1 increments are allowed.")
            else:
                await self.config.guild(message.guild).previous_number.set(int(content))
                await self.react_with_random_emoji(message)

    async def react_with_random_emoji(self, message):
        emojis = await self.bot.fetch_guild_emojis(message.guild)
        random_emoji = random.choice(emojis)
        await message.add_reaction(random_emoji)

def setup(bot):
    bot.add_cog(InfiniCount(bot))
