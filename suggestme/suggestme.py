#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands, Config
from discord import Embed, utils
from datetime import datetime


class SuggestMe(commands.Cog):
    """A suggestion system for server members."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8765432109, force_registration=True)
        default_guild = {
            "suggestion_count": 0,
            "suggest_channel_id": None,
            "output_channel_id": None,
            "required_role": None,
            "staff_role": None,
            "required_upvotes": 4
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def suggest(self, ctx, *, suggestion: str = None):
        """Submit a suggestion for the server."""
        if suggestion is None:
            await ctx.send_help(ctx.command)
            return

        settings = await self.config.guild(ctx.guild).all()

        # Check channel restriction
        if settings["suggest_channel_id"]:
            if ctx.channel.id != settings["suggest_channel_id"]:
                channel = ctx.guild.get_channel(settings["suggest_channel_id"])
                if channel:
                    await ctx.send(f"Please use this command in {channel.mention}.", delete_after=10)
                return

        # Check required role
        if settings["required_role"]:
            role = ctx.guild.get_role(settings["required_role"])
            if role and role not in ctx.author.roles:
                await ctx.send(f"You need the {role.name} role to submit suggestions.", delete_after=10)
                return

        # Increment and get suggestion count
        suggestion_count = settings["suggestion_count"] + 1
        await self.config.guild(ctx.guild).suggestion_count.set(suggestion_count)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        embed = Embed(
            title=f"Suggestion #{suggestion_count}",
            description=suggestion,
            color=0x800080
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Suggested on {timestamp}")

        message = await ctx.send(embed=embed)

        # Add voting reactions
        for emoji in ["\U0001F44D", "\U0001F44E", "\u2705", "\u274C"]:
            try:
                await message.add_reaction(emoji)
            except discord.Forbidden:
                pass

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    @suggest.command(name="channel")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where suggestions must be submitted."""
        if channel:
            await self.config.guild(ctx.guild).suggest_channel_id.set(channel.id)
            await ctx.send(f"Suggestions must now be submitted in {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).suggest_channel_id.set(None)
            await ctx.send("Suggestions can now be submitted in any channel.")

    @suggest.command(name="output")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_output(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where approved suggestions are posted."""
        if channel:
            await self.config.guild(ctx.guild).output_channel_id.set(channel.id)
            await ctx.send(f"Approved suggestions will be posted in {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).output_channel_id.set(None)
            await ctx.send("Output channel cleared.")

    @suggest.command(name="role")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_role(self, ctx, role: discord.Role = None):
        """Set the role required to submit suggestions."""
        if role:
            await self.config.guild(ctx.guild).required_role.set(role.id)
            await ctx.send(f"The {role.name} role is now required to submit suggestions.")
        else:
            await self.config.guild(ctx.guild).required_role.set(None)
            await ctx.send("No role is required to submit suggestions.")

    @suggest.command(name="staff")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_staff(self, ctx, role: discord.Role = None):
        """Set the staff role that can approve/deny suggestions."""
        if role:
            await self.config.guild(ctx.guild).staff_role.set(role.id)
            await ctx.send(f"The {role.name} role can now manage suggestions.")
        else:
            await self.config.guild(ctx.guild).staff_role.set(None)
            await ctx.send("Staff role cleared.")

    @suggest.command(name="upvotes")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_upvotes(self, ctx, count: int):
        """Set the number of upvotes required for auto-approval."""
        if count < 1 or count > 100:
            await ctx.send("Upvote count must be between 1 and 100.")
            return
        await self.config.guild(ctx.guild).required_upvotes.set(count)
        await ctx.send(f"Suggestions will be auto-approved after {count} upvotes.")

    @suggest.command(name="settings")
    @commands.admin_or_permissions(manage_guild=True)
    async def suggest_settings(self, ctx):
        """View current suggestion settings."""
        settings = await self.config.guild(ctx.guild).all()

        suggest_channel = ctx.guild.get_channel(settings["suggest_channel_id"]) if settings["suggest_channel_id"] else None
        output_channel = ctx.guild.get_channel(settings["output_channel_id"]) if settings["output_channel_id"] else None
        required_role = ctx.guild.get_role(settings["required_role"]) if settings["required_role"] else None
        staff_role = ctx.guild.get_role(settings["staff_role"]) if settings["staff_role"] else None

        embed = Embed(title="Suggestion Settings", color=0x800080)
        embed.add_field(name="Total Suggestions", value=str(settings["suggestion_count"]), inline=True)
        embed.add_field(name="Required Upvotes", value=str(settings["required_upvotes"]), inline=True)
        embed.add_field(name="Suggest Channel", value=suggest_channel.mention if suggest_channel else "Any", inline=True)
        embed.add_field(name="Output Channel", value=output_channel.mention if output_channel else "Not set", inline=True)
        embed.add_field(name="Required Role", value=required_role.name if required_role else "None", inline=True)
        embed.add_field(name="Staff Role", value=staff_role.name if staff_role else "None", inline=True)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle suggestion approval via reactions."""
        if user.bot:
            return
        if not reaction.message.guild:
            return
        if not reaction.message.embeds:
            return

        embed = reaction.message.embeds[0]
        if not embed.title or not embed.title.startswith("Suggestion #"):
            return

        settings = await self.config.guild(reaction.message.guild).all()

        # Check staff permissions for approve/deny
        is_staff = False
        if settings["staff_role"]:
            staff_role = reaction.message.guild.get_role(settings["staff_role"])
            if staff_role and staff_role in user.roles:
                is_staff = True
        elif user.guild_permissions.manage_guild:
            is_staff = True

        emoji = str(reaction.emoji)

        if emoji == "\U0001F44D":
            # Check for auto-approval
            thumbs_up = next((r for r in reaction.message.reactions if str(r.emoji) == "\U0001F44D"), None)
            if thumbs_up and thumbs_up.count >= settings["required_upvotes"]:
                await self._approve_suggestion(reaction.message, embed, thumbs_up.count, settings)

        elif emoji == "\u2705" and is_staff:
            # Staff approval
            await self._approve_suggestion(reaction.message, embed, 0, settings, staff_approved=True)

        elif emoji == "\u274C" and is_staff:
            # Staff denial
            try:
                await reaction.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

    async def _approve_suggestion(self, message, embed, upvotes, settings, staff_approved=False):
        """Move approved suggestion to output channel."""
        output_channel_id = settings["output_channel_id"]
        if output_channel_id:
            output_channel = message.guild.get_channel(output_channel_id)
            if output_channel:
                footer_text = embed.footer.text or ""
                if staff_approved:
                    footer_text += " | Staff Approved"
                else:
                    footer_text += f" | Approved with {upvotes} upvotes"
                embed.set_footer(text=footer_text)
                embed.color = 0x00ff00
                try:
                    await output_channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
