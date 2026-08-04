#
# Custom Commands — simple MEE6-style text replies triggered by prefix + name.
#

from __future__ import annotations

import re
from typing import Dict

import discord
from discord import Embed
from redbot.core import Config, commands

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{2,32}$")


class Customcommands(commands.Cog):
    """Guild custom commands: `[p]name` replies with saved text."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xCC0510C0, force_registration=True)
        # commands: {name_lower: {"response": str, "owner": int, "embed": bool}}
        self.config.register_guild(commands={})

    async def red_delete_data_for_user(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return
        for guild in self.bot.guilds:
            cmds = await self.config.guild(guild).commands()
            changed = False
            for name, data in list(cmds.items()):
                if data.get("owner") == user_id:
                    data["owner"] = None
                    changed = True
            if changed:
                await self.config.guild(guild).commands.set(cmds)

    async def _get_cmds(self, guild: discord.Guild) -> Dict[str, dict]:
        return await self.config.guild(guild).commands()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return
        # Don't steal real bot commands — only fire if no command matched... 
        # Actually we run before process_commands finishes; use prefix strip.
        try:
            prefixes = await self.bot.get_prefix(message)
        except Exception:
            return
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        content = message.content
        used = None
        for p in sorted(prefixes, key=len, reverse=True):
            if content.startswith(p):
                used = p
                break
        if used is None:
            return
        body = content[len(used) :].strip()
        if not body:
            return
        parts = body.split()
        if len(parts) != 1:
            return  # bare name only — avoids stealing real commands with args
        name = parts[0].lower()
        if self.bot.get_command(name):
            return
        cmds = await self._get_cmds(message.guild)
        data = cmds.get(name)
        if not data:
            return
        response = data.get("response") or ""
        if not response:
            return
        try:
            if data.get("embed"):
                await message.channel.send(
                    embed=Embed(description=response[:4000], color=0x3498DB)
                )
            else:
                await message.channel.send(response[:2000])
        except discord.HTTPException:
            pass

    @commands.hybrid_group(name="cc", aliases=["customcom", "tag", "tags"])
    @commands.guild_only()
    async def cc(self, ctx: commands.Context):
        """Custom commands (tags). Use `[p]name` after creating one."""
        if ctx.invoked_subcommand is None:
            emb = Embed(
                title="📝 Custom Commands",
                description=(
                    f"`{ctx.clean_prefix}cc add <name> <response>`\n"
                    f"`{ctx.clean_prefix}cc edit <name> <response>`\n"
                    f"`{ctx.clean_prefix}cc remove <name>`\n"
                    f"`{ctx.clean_prefix}cc list`\n"
                    f"`{ctx.clean_prefix}cc show <name>`\n"
                    f"`{ctx.clean_prefix}cc embed <name> <true/false>`\n\n"
                    f"Then type `{ctx.clean_prefix}<name>` to trigger."
                ),
                color=0x3498DB,
            )
            await ctx.send(embed=emb)

    @cc.command(name="add")
    @commands.admin_or_permissions(manage_guild=True)
    async def cc_add(self, ctx: commands.Context, name: str, *, response: str):
        """Create a custom command."""
        name = name.lower()
        if not _NAME_RE.match(name):
            await ctx.send("Name must be 2–32 chars: letters, numbers, `_` or `-`.")
            return
        if self.bot.get_command(name):
            await ctx.send("That name is already a real bot command.")
            return
        cmds = await self._get_cmds(ctx.guild)
        if name in cmds:
            await ctx.send("That command already exists. Use `cc edit`.")
            return
        if len(cmds) >= 100:
            await ctx.send("Max 100 custom commands per server.")
            return
        cmds[name] = {
            "response": response[:1900],
            "owner": ctx.author.id,
            "embed": False,
        }
        await self.config.guild(ctx.guild).commands.set(cmds)
        await ctx.send(f"Created `{ctx.clean_prefix}{name}`.")

    @cc.command(name="edit")
    @commands.admin_or_permissions(manage_guild=True)
    async def cc_edit(self, ctx: commands.Context, name: str, *, response: str):
        """Edit an existing custom command."""
        name = name.lower()
        cmds = await self._get_cmds(ctx.guild)
        if name not in cmds:
            await ctx.send("Unknown custom command.")
            return
        cmds[name]["response"] = response[:1900]
        await self.config.guild(ctx.guild).commands.set(cmds)
        await ctx.send(f"Updated `{ctx.clean_prefix}{name}`.")

    @cc.command(name="remove", aliases=["delete", "del"])
    @commands.admin_or_permissions(manage_guild=True)
    async def cc_remove(self, ctx: commands.Context, name: str):
        """Delete a custom command."""
        name = name.lower()
        cmds = await self._get_cmds(ctx.guild)
        if name not in cmds:
            await ctx.send("Unknown custom command.")
            return
        del cmds[name]
        await self.config.guild(ctx.guild).commands.set(cmds)
        await ctx.send(f"Removed `{name}`.")

    @cc.command(name="list")
    async def cc_list(self, ctx: commands.Context):
        """List custom commands in this server."""
        cmds = await self._get_cmds(ctx.guild)
        if not cmds:
            await ctx.send("No custom commands yet.")
            return
        names = ", ".join(f"`{n}`" for n in sorted(cmds))
        await ctx.send(embed=Embed(title="Custom commands", description=names[:4000], color=0x3498DB))

    @cc.command(name="show")
    async def cc_show(self, ctx: commands.Context, name: str):
        """Show the response text for a custom command."""
        name = name.lower()
        cmds = await self._get_cmds(ctx.guild)
        data = cmds.get(name)
        if not data:
            await ctx.send("Unknown custom command.")
            return
        await ctx.send(
            embed=Embed(
                title=f"{ctx.clean_prefix}{name}",
                description=data.get("response", "")[:4000],
                color=0x3498DB,
            )
        )

    @cc.command(name="embed")
    @commands.admin_or_permissions(manage_guild=True)
    async def cc_embed(self, ctx: commands.Context, name: str, enabled: bool):
        """Send the response as an embed instead of plain text."""
        name = name.lower()
        cmds = await self._get_cmds(ctx.guild)
        if name not in cmds:
            await ctx.send("Unknown custom command.")
            return
        cmds[name]["embed"] = enabled
        await self.config.guild(ctx.guild).commands.set(cmds)
        await ctx.send(f"`{name}` embed mode: **{enabled}**")
