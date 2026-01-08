#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

import discord
from redbot.core import commands

class Scanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_check = False  # Toggle for autoscan
        self.target_channel_id = None  # Channel ID to post results

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def cog_unload(self):
        # Clean up tasks if needed
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.auto_check:
            await self.scan_user(member)

    async def scan_user(self, user):
        # Check if a target channel is set
        if self.target_channel_id:
            # Get the channel to post results
            target_channel = user.guild.get_channel(self.target_channel_id)

            # Check if the channel exists and the bot has permission to send messages
            if target_channel and target_channel.permissions_for(user.guild.me).send_messages:
                # Build the command to check trust levels using AltDentifier
                command = f"ccaltcheck {user.mention}"  # Replace [p] with your actual prefix

                try:
                    # Execute the command silently
                    _, results, _ = await self.bot.get_context(user.message).invoke(self.bot.get_command("altcheck"), command)
                    # Post the results in the specified channel
                    await target_channel.send(f"Results for {user.mention}: {results}")
                except Exception as e:
                    print(f"An error occurred while checking trust levels for {user.mention}: {e}")

    @commands.command(name="autoscan")
    async def toggle_check(self, ctx, status: str):
        """Toggle autoscan on/off."""
        if status.lower() in ["on", "off"]:
            self.auto_check = status.lower() == "on"
            await ctx.send(f"Auto-Scan {'enabled' if self.auto_check else 'disabled'}.")
        else:
            await ctx.send("Invalid status. Use 'on' or 'off'.")

    @commands.command(name="scannerchannel")
    async def set_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for posting results."""
        if channel:
            self.target_channel_id = channel.id
            await ctx.send(f"Results will be posted in {channel.mention}.")
        else:
            await ctx.send("Invalid channel. Please provide a valid channel.")

    @commands.command(name="scanner")
    async def scanner_help(self, ctx):
        """Displays help for the Scanner cog."""
        help_embed = discord.Embed(
            title="Scanner Commands",
            description=(
                f"**{ctx.prefix}autoscan <on/off>**: Toggle autoscan on/off.\n"
                f"**{ctx.prefix}scannerchannel <channel>**: Set the channel for posting results.\n"
            ),
            color=discord.Color.blue(),
        )
        await ctx.send(embed=help_embed)