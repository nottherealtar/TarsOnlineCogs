#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands, Config
import asyncio


class VerifyAll(commands.Cog):
    """Mass verification tool for server members."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5678901234, force_registration=True)
        default_guild = {
            "verified_role_id": None
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def verifyall(self, ctx, member: discord.Member = None):
        """
        Verify members by giving them the verified role.

        If a member is specified, only verify that member.
        If no member is specified, verify all unverified members.
        """
        verified_role_id = await self.config.guild(ctx.guild).verified_role_id()

        if not verified_role_id:
            # Try to find a role named "Verified"
            verified_role = discord.utils.get(ctx.guild.roles, name="Verified")
            if not verified_role:
                await ctx.send("No verified role is set. Use `verifyall setrole @role` to set one.")
                return
        else:
            verified_role = ctx.guild.get_role(verified_role_id)
            if not verified_role:
                await ctx.send("The configured verified role no longer exists. Please set a new one.")
                return

        # Check bot permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("I don't have permission to manage roles.")
            return

        if verified_role >= ctx.guild.me.top_role:
            await ctx.send("The verified role is higher than or equal to my highest role. I cannot assign it.")
            return

        if member:
            # Verify single member
            if verified_role in member.roles:
                await ctx.send(f"{member.display_name} is already verified.")
                return
            try:
                await member.add_roles(verified_role, reason=f"Verified by {ctx.author}")
                await ctx.send(f"{member.display_name} has been verified.")
            except discord.Forbidden:
                await ctx.send(f"Failed to verify {member.display_name}. Check my permissions.")
        else:
            # Verify all unverified members
            unverified = [m for m in ctx.guild.members if not m.bot and verified_role not in m.roles]

            if not unverified:
                await ctx.send("All members are already verified.")
                return

            total = len(unverified)
            verified_count = 0
            failed_count = 0

            progress_message = await ctx.send(f"Verifying members: 0/{total}")

            for i, member in enumerate(unverified):
                try:
                    await member.add_roles(verified_role, reason=f"Mass verification by {ctx.author}")
                    verified_count += 1
                except discord.Forbidden:
                    failed_count += 1

                # Update progress every 10 members
                if (i + 1) % 10 == 0 or i == total - 1:
                    try:
                        await progress_message.edit(content=f"Verifying members: {i + 1}/{total}")
                    except discord.NotFound:
                        pass

                # Rate limit protection
                await asyncio.sleep(0.5)

            result = f"Verification complete. Verified: {verified_count}/{total}"
            if failed_count:
                result += f" (Failed: {failed_count})"

            try:
                await progress_message.edit(content=result)
            except discord.NotFound:
                await ctx.send(result)

    @verifyall.command(name="setrole")
    @commands.has_permissions(manage_roles=True)
    async def verifyall_setrole(self, ctx, role: discord.Role):
        """Set the role to use for verification."""
        if role >= ctx.guild.me.top_role:
            await ctx.send("That role is higher than or equal to my highest role. I cannot assign it.")
            return
        await self.config.guild(ctx.guild).verified_role_id.set(role.id)
        await ctx.send(f"Verified role set to {role.name}.")

    @verifyall.command(name="status")
    async def verifyall_status(self, ctx):
        """Show verification status for the server."""
        verified_role_id = await self.config.guild(ctx.guild).verified_role_id()

        if not verified_role_id:
            verified_role = discord.utils.get(ctx.guild.roles, name="Verified")
        else:
            verified_role = ctx.guild.get_role(verified_role_id)

        if not verified_role:
            await ctx.send("No verified role is configured.")
            return

        total_humans = sum(1 for m in ctx.guild.members if not m.bot)
        verified = sum(1 for m in ctx.guild.members if not m.bot and verified_role in m.roles)
        unverified = total_humans - verified

        embed = discord.Embed(title="Verification Status", color=0x00ff00)
        embed.add_field(name="Verified Role", value=verified_role.mention, inline=True)
        embed.add_field(name="Total Humans", value=str(total_humans), inline=True)
        embed.add_field(name="Verified", value=str(verified), inline=True)
        embed.add_field(name="Unverified", value=str(unverified), inline=True)
        await ctx.send(embed=embed)
