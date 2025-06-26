import discord
from redbot.core import Config, commands, checks
import aiohttp
import json
import asyncio
import logging

log = logging.getLogger("red.nottherealtar.lessonplanner")


class LessonPlannerCog(commands.Cog):
    """Cog to generate university lesson plans as PDFs via n8n workflow."""

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        
        default_global = {
            "n8n_url": "https://0d09-102-135-142-207.ngrok-free.app/lesson-plan-pdf",  # Default ngrok URL
            "allowed_users": [985226198508511302, 552199165153902604]  # Authorized user IDs
        }
        self.config.register_global(**default_global)
        self.config.register_guild(plans={})  # Store plans per guild
        
        self.session = aiohttp.ClientSession()
        self.lock = asyncio.Lock()  # Prevent race conditions

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.group(autohelp=True)
    @checks.is_owner()
    async def lessonplanset(self, ctx):
        """Configuration commands for Lesson Planner cog."""
        pass

    @lessonplanset.command(name="url")
    async def set_n8n_url(self, ctx, *, url=None):
        """Set or view the n8n webhook URL.
        
        Example: [p]lessonplanset url http://localhost:5678/webhook-test/lesson-plan-pdf
        """
        if url is None:
            current_url = await self.config.n8n_url()
            if current_url:
                # Don't show the full URL for security
                masked_url = current_url[:20] + "..." if len(current_url) > 20 else current_url
                await ctx.send(f"Current n8n URL: `{masked_url}`")
            else:
                await ctx.send("No n8n URL configured. Use `[p]lessonplanset url <url>` to set it.")
            return
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            await ctx.send("URL must start with http:// or https://")
            return
            
        await self.config.n8n_url.set(url)
        await ctx.send("✅ n8n webhook URL has been set successfully.")

    @lessonplanset.command(name="test")
    async def test_connection(self, ctx):
        """Test the connection to the n8n webhook."""
        n8n_url = await self.config.n8n_url()
        if not n8n_url:
            await ctx.send("❌ No n8n URL configured. Use `[p]lessonplanset url <url>` first.")
            return
            
        try:
            test_payload = {"text": "Connection test", "user_id": "test"}
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {"Content-Type": "application/json"}
            
            # Add ngrok bypass header if using ngrok
            if "ngrok" in n8n_url:
                headers["ngrok-skip-browser-warning"] = "true"
                
            async with self.session.post(n8n_url, json=test_payload, timeout=timeout, headers=headers) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    await ctx.send(f"✅ Connection test successful! Response: {response_text[:200]}...")
                else:
                    await ctx.send(f"⚠️ Connection test failed: HTTP {resp.status}")
        except asyncio.TimeoutError:
            await ctx.send("❌ Connection test failed: Request timed out (check if n8n is running and accessible)")
        except aiohttp.ClientConnectorError as e:
            await ctx.send(f"❌ Connection test failed: Cannot connect to server. Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Connection test failed: {str(e)}")

    @lessonplanset.command(name="debug")
    async def debug_connection(self, ctx, *, test_url=None):
        """Debug connection to a specific URL without saving it.
        
        Example: [p]lessonplanset debug http://localhost:5678/webhook-test/lesson-plan-pdf
        """
        if not test_url:
            await ctx.send("Please provide a URL to test: `[p]lessonplanset debug <url>`")
            return
            
        try:
            test_payload = {"text": "Debug connection test", "user_id": "debug"}
            await ctx.send(f"🔍 Testing connection to: `{test_url}`...")
            
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {"Content-Type": "application/json"}
            
            # Add ngrok bypass header if using ngrok
            if "ngrok" in test_url:
                headers["ngrok-skip-browser-warning"] = "true"
                
            async with self.session.post(test_url, json=test_payload, timeout=timeout, headers=headers) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    await ctx.send(f"✅ Debug test successful! Response: {response_text[:200]}...")
                else:
                    await ctx.send(f"⚠️ Debug test failed: HTTP {resp.status}")
        except asyncio.TimeoutError:
            await ctx.send("❌ Debug test failed: Request timed out")
        except aiohttp.ClientConnectorError as e:
            await ctx.send(f"❌ Debug test failed: Cannot connect. Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Debug test failed: {str(e)}")

    @lessonplanset.command(name="ngrok")
    async def update_ngrok_url(self, ctx, *, ngrok_domain=None):
        """Update the ngrok domain while keeping the /lesson-plan-pdf path.
        
        Example: [p]lessonplanset ngrok 0d09-102-135-142-207.ngrok-free.app
        Or: [p]lessonplanset ngrok https://0d09-102-135-142-207.ngrok-free.app
        """
        if not ngrok_domain:
            await ctx.send("Please provide your ngrok domain: `[p]lessonplanset ngrok <domain>`")
            return
            
        # Clean up the input - remove protocol if provided
        if ngrok_domain.startswith(('http://', 'https://')):
            ngrok_domain = ngrok_domain.split('://', 1)[1]
            
        # Remove trailing slash if present
        ngrok_domain = ngrok_domain.rstrip('/')
        
        # Build the full URL
        full_url = f"https://{ngrok_domain}/lesson-plan-pdf"
        
        # Save the URL
        await self.config.n8n_url.set(full_url)
        await ctx.send(f"✅ ngrok URL updated to: `{full_url}`")
        
        # Automatically test the connection
        await ctx.send("🔍 Testing the new URL...")
        try:
            test_payload = {"text": "Auto-test after ngrok update", "user_id": "test"}
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true"
            }
            
            async with self.session.post(full_url, json=test_payload, timeout=timeout, headers=headers) as resp:
                if resp.status == 200:
                    await ctx.send("✅ Connection test successful!")
                else:
                    await ctx.send(f"⚠️ Connection test failed: HTTP {resp.status}")
        except Exception as e:
            await ctx.send(f"❌ Connection test failed: {str(e)}")

    @commands.command()
    @commands.cooldown(2, 60, commands.BucketType.user)  # Limit to 2 uses per minute
    async def plan(self, ctx: commands.Context, *, text: str):
        """Create a lesson plan (e.g., !plan Learn 3D Animation 2 months)"""
        # Check if user is authorized
        allowed_users = await self.config.allowed_users()
        if ctx.author.id not in allowed_users:
            await ctx.send("❌ You are not authorized to use this command.")
            return
            
        n8n_url = await self.config.n8n_url()
        if not n8n_url:
            await ctx.send("❌ Lesson planner is not configured. Please contact the bot owner.")
            return
            
        async with self.lock:
            try:
                payload = {"text": text, "user_id": str(ctx.author.id)}
                headers = {"Content-Type": "application/json"}
                
                # Add ngrok bypass header if using ngrok
                if "ngrok" in n8n_url:
                    headers["ngrok-skip-browser-warning"] = "true"
                    
                async with self.session.post(n8n_url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "content" in data:
                            await ctx.send(data["content"])
                        else:
                            await ctx.send("Unexpected response format. Please try again.")
                    else:
                        await ctx.send(f"Error: HTTP {resp.status} - Please contact support.")
            except aiohttp.ClientConnectorError:
                await ctx.send("Network error. Please try again later.")
            except Exception as e:
                log.exception("Error in lesson plan generation:")
                await ctx.send(f"Unexpected error: {str(e)}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Handle command-specific errors."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command on cooldown. Try again in {error.retry_after:.0f}s.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: !plan <topic> <duration e.g., 2 months>")

    @lessonplanset.command(name="users")
    async def manage_users(self, ctx, action=None, user_id=None):
        """Manage authorized users for the lesson planner.
        
        Actions: add, remove, list
        Example: [p]lessonplanset users add 123456789012345678
        """
        if action is None:
            await ctx.send("Available actions: `add`, `remove`, `list`\nExample: `[p]lessonplanset users list`")
            return
            
        allowed_users = await self.config.allowed_users()
        
        if action.lower() == "list":
            if allowed_users:
                user_list = "\n".join([f"• <@{user_id}> ({user_id})" for user_id in allowed_users])
                await ctx.send(f"**Authorized Users:**\n{user_list}")
            else:
                await ctx.send("No authorized users configured.")
                
        elif action.lower() == "add":
            if user_id is None:
                await ctx.send("Please provide a user ID: `[p]lessonplanset users add <user_id>`")
                return
            try:
                user_id = int(user_id)
            except ValueError:
                await ctx.send("Invalid user ID format. Please provide a numeric Discord user ID.")
                return
            if user_id not in allowed_users:
                allowed_users.append(user_id)
                await self.config.allowed_users.set(allowed_users)
                await ctx.send(f"✅ Added <@{user_id}> to authorized users.")
            else:
                await ctx.send(f"<@{user_id}> is already authorized.")
                
        elif action.lower() == "remove":
            if user_id is None:
                await ctx.send("Please provide a user ID: `[p]lessonplanset users remove <user_id>`")
                return
            try:
                user_id = int(user_id)
            except ValueError:
                await ctx.send("Invalid user ID format. Please provide a numeric Discord user ID.")
                return
            if user_id in allowed_users:
                allowed_users.remove(user_id)
                await self.config.allowed_users.set(allowed_users)
                await ctx.send(f"✅ Removed <@{user_id}> from authorized users.")
            else:
                await ctx.send(f"<@{user_id}> is not in the authorized users list.")
        else:
            await ctx.send("Invalid action. Use: `add`, `remove`, or `list`")

async def setup(bot):
    await bot.add_cog(LessonPlannerCog(bot))