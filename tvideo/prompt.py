import discord
from redbot.core import commands, Config
import aiohttp
import asyncio
import json
from typing import Optional

class TVideo(commands.Cog):
    """AI Video Generation Cog using Pipedream webhooks"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_global = {
            "pipedream_webhook_url": None,
            "api_key": None
        }
        default_guild = {
            "webhook_channel": None
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    @commands.group(invoke_without_command=True)
    async def tvideo(self, ctx):
        """Base command for TVideo cog configuration and usage."""
        embed = discord.Embed(
            title="🎬 TVideo - AI Video Generator",
            description="Generate videos using AI through Pipedream integration",
            color=0x7289DA
        )
        embed.add_field(
            name="Commands",
            value="`[p]request <prompt>` - Generate a video with your prompt\n"
                  "`[p]tvideo setup` - Configure the cog (Admin only)\n"
                  "`[p]tvideo status` - Check configuration status",
            inline=False
        )
        embed.add_field(
            name="Note",
            value="This cog requires proper setup with Pipedream webhook integration.\n"
                  "Videos are generated asynchronously and delivered via webhook.",
            inline=False
        )
        embed.set_footer(text="Videos are generated asynchronously and delivered via webhook")
        await ctx.send(embed=embed)

    @tvideo.command(name="setup")
    @commands.admin_or_permissions(administrator=True)
    async def setup_tvideo(self, ctx):
        """Setup TVideo configuration (Admin only)"""
        embed = discord.Embed(
            title="🔧 TVideo Setup",
            description="Configure your API settings for video generation",
            color=0xFFA500
        )
        embed.add_field(
            name="Configuration Commands",
            value="`[p]tvideo setwebhook <url>` - Set Pipedream webhook URL\n"
                  "`[p]tvideo setkey <api_key>` - Set API key (optional)\n"
                  "`[p]tvideo setchannel <channel>` - Set notification channel\n"
                  "`[p]tvideo status` - Check configuration status",
            inline=False
        )
        embed.add_field(
            name="Usage",
            value="`[p]request <your_prompt>` - Generate a video",
            inline=False
        )
        await ctx.send(embed=embed)

    @tvideo.command(name="setwebhook")
    @commands.admin_or_permissions(administrator=True)
    async def set_webhook(self, ctx, url: str):
        """Set the Pipedream webhook URL"""
        if not url.startswith("https://"):
            await ctx.send("❌ Webhook URL must start with https://")
            return
        
        await self.config.pipedream_webhook_url.set(url)
        await ctx.send("✅ Pipedream webhook URL has been set successfully!")
        # Delete the command message for security
        try:
            await ctx.message.delete()
        except:
            pass

    @tvideo.command(name="setkey")
    @commands.admin_or_permissions(administrator=True)
    async def set_api_key(self, ctx, api_key: str):
        """Set the API key for authentication"""
        await self.config.api_key.set(api_key)
        await ctx.send("✅ API key has been set successfully!")
        # Delete the message for security
        try:
            await ctx.message.delete()
        except:
            pass

    @tvideo.command(name="setchannel")
    @commands.admin_or_permissions(administrator=True)
    async def set_webhook_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for notifications"""
        channel = channel or ctx.channel
        await self.config.guild(ctx.guild).webhook_channel.set(channel.id)
        await ctx.send(f"✅ Notification channel set to {channel.mention}")

    @tvideo.command(name="status")
    async def check_status(self, ctx):
        """Check the configuration status of TVideo"""
        webhook_url = await self.config.pipedream_webhook_url()
        api_key = await self.config.api_key()
        webhook_channel_id = await self.config.guild(ctx.guild).webhook_channel()
        
        embed = discord.Embed(
            title="📊 TVideo Configuration Status",
            color=0x00FF00 if webhook_url else 0xFF0000
        )
        
        embed.add_field(
            name="Pipedream Webhook",
            value="✅ Configured" if webhook_url else "❌ Not configured - use `[p]tvideo setwebhook <url>`",
            inline=False
        )
        embed.add_field(
            name="API Key",
            value="✅ Configured" if api_key else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="Notification Channel",
            value=f"✅ <#{webhook_channel_id}>" if webhook_channel_id else "❌ Not configured",
            inline=True
        )
        
        embed.add_field(
            name="Ready to Use",
            value="✅ Send video requests with `[p]request <prompt>`" if webhook_url else "❌ Configure webhook URL first with `[p]tvideo setwebhook <url>`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="request")
    async def request_video(self, ctx, *, prompt: str):
        """Request an AI-generated video with the given prompt"""
        await self._process_video_request(ctx, prompt)

    async def _process_video_request(self, ctx, prompt: str):
        """Process a video generation request"""
        # Get the webhook URL
        webhook_url = await self.config.pipedream_webhook_url()
        if not webhook_url:
            embed = discord.Embed(
                title="❌ Configuration Error",
                description="TVideo webhook URL is not configured. Please ask an administrator to run `[p]tvideo setwebhook <url>`",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Check prompt length
        if len(prompt) > 500:
            await ctx.send("❌ Prompt is too long. Please keep it under 500 characters.")
            return

        # Create initial response
        embed = discord.Embed(
            title="🎬 Video Generation Request",
            description=f"**Prompt:** {prompt}",
            color=0xFFFF00
        )
        embed.add_field(
            name="Status",
            value="🔄 Sending request to AI model...",
            inline=False
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        # Send initial message
        message = await ctx.send(embed=embed)        # Prepare request data for Pipedream
        request_data = {
            "prompt": prompt,
            "user_id": str(ctx.author.id),
            "user_name": ctx.author.display_name,
            "guild_id": str(ctx.guild.id),
            "channel_id": str(ctx.channel.id),
            "message_id": str(message.id)
        }

        # Add API key if configured
        api_key = await self.config.api_key()
        if api_key:
            request_data["api_key"] = api_key

        try:
            # Send request to Pipedream
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        # Update embed to show success
                        embed.set_field_at(
                            0,
                            name="Status",
                            value="✅ Request sent successfully! Video generation started.",
                            inline=False
                        )
                        embed.color = 0x00FF00
                        
                    else:
                        # Update embed to show error
                        embed.set_field_at(
                            0,
                            name="Status",
                            value=f"❌ Request failed with status code: {response.status}",
                            inline=False
                        )
                        embed.color = 0xFF0000
                    
                    await message.edit(embed=embed)

        except Exception as e:
            # Update embed to show error
            embed.set_field_at(
                0,
                name="Status",
                value=f"❌ Error sending request: {str(e)[:100]}...",
                inline=False
            )
            embed.color = 0xFF0000
            await message.edit(embed=embed)

def setup(bot):
    bot.add_cog(TVideo(bot))