#
# Level Roles — MEE6-style role rewards using ServerAssistant XP (no second leveling system).
#

from __future__ import annotations

import logging
from typing import Dict, Optional

import discord
from discord import Embed
from redbot.core import Config, commands

log = logging.getLogger("red.nottherealtar.levelroles")


def _level_from_xp(xp: int) -> int:
    """Must match serverassistant._level_from_xp."""
    if xp < 0:
        xp = 0
    return int((xp / 100) ** 0.5)


class Levelroles(commands.Cog):
    """Grant roles at ServerAssistant level thresholds. Requires `serverassistant` loaded."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x1E7E1801, force_registration=True)
        # rewards: {"5": role_id, "10": role_id, ...}
        self.config.register_guild(rewards={}, announce_channel=None, stack=True)

    async def red_delete_data_for_user(self, **kwargs):
        return

    def _sa(self):
        return self.bot.get_cog("ServerAssistant")

    async def _member_level(self, member: discord.Member) -> Optional[int]:
        sa = self._sa()
        if sa is None:
            return None
        xp = await sa.config.member(member).xp()
        return _level_from_xp(int(xp))

    async def sync_roles(
        self, member: discord.Member, *, announce: bool = False, old_level: Optional[int] = None
    ) -> list[discord.Role]:
        """Ensure member has all reward roles for their current level. Returns newly granted roles."""
        if member.bot or not member.guild:
            return []
        level = await self._member_level(member)
        if level is None:
            return []

        rewards: Dict[str, int] = await self.config.guild(member.guild).rewards()
        if not rewards:
            return []

        stack = await self.config.guild(member.guild).stack()
        granted: list[discord.Role] = []
        to_add: list[discord.Role] = []
        to_remove: list[discord.Role] = []

        parsed: list[tuple[int, discord.Role]] = []
        for lvl_str, role_id in rewards.items():
            try:
                need = int(lvl_str)
            except (TypeError, ValueError):
                continue
            role = member.guild.get_role(int(role_id))
            if role is not None:
                parsed.append((need, role))

        highest_ok = max((n for n, _ in parsed if level >= n), default=None)

        for need, role in parsed:
            qualifies = level >= need if stack else (highest_ok is not None and need == highest_ok)
            has = role in member.roles
            if qualifies and not has:
                to_add.append(role)
                if old_level is None or need > old_level:
                    granted.append(role)
            elif not qualifies and has:
                to_remove.append(role)

        me = member.guild.me
        if me is None:
            return []

        for role in to_add:
            if role >= me.top_role or not me.guild_permissions.manage_roles:
                continue
            try:
                await member.add_roles(role, reason=f"Level roles: reached level {level}")
            except discord.HTTPException as e:
                log.debug("Could not add %s to %s: %s", role.id, member.id, e)

        for role in to_remove:
            if role >= me.top_role:
                continue
            try:
                await member.remove_roles(role, reason="Level roles: stack=False sync")
            except discord.HTTPException:
                pass

        if announce and granted:
            ch_id = await self.config.guild(member.guild).announce_channel()
            channel = member.guild.get_channel(ch_id) if ch_id else None
            if isinstance(channel, discord.TextChannel):
                names = ", ".join(r.mention for r in granted)
                try:
                    await channel.send(
                        f"🎉 {member.mention} reached **level {level}** and unlocked {names}!"
                    )
                except discord.HTTPException:
                    pass

        return granted

    @commands.Cog.listener()
    async def on_tars_xp_gain(
        self, member: discord.Member, new_xp: int, old_level: int, new_level: int
    ):
        if new_level <= old_level:
            # Still sync in case rewards were added after they leveled
            await self.sync_roles(member, announce=False)
            return
        await self.sync_roles(member, announce=True, old_level=old_level)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.sync_roles(member, announce=False)

    @commands.hybrid_group(name="levelrole", aliases=["levelroles", "xprole"])
    @commands.guild_only()
    async def levelrole(self, ctx: commands.Context):
        """MEE6-style level role rewards (uses ServerAssistant XP)."""
        if ctx.invoked_subcommand is None:
            emb = Embed(
                title="🎖️ Level Roles",
                description=(
                    "Awards roles when members hit ServerAssistant levels.\n"
                    f"**Requires:** `serverassistant` loaded + `[p]serverassistant level enable`\n\n"
                    f"`{ctx.clean_prefix}levelrole add <level> @role`\n"
                    f"`{ctx.clean_prefix}levelrole remove <level>`\n"
                    f"`{ctx.clean_prefix}levelrole list`\n"
                    f"`{ctx.clean_prefix}levelrole sync [@member]`\n"
                    f"`{ctx.clean_prefix}levelrole announce #channel`\n"
                    f"`{ctx.clean_prefix}levelrole stack <true/false>`"
                ),
                color=0xF1C40F,
            )
            sa = self._sa()
            emb.set_footer(
                text="ServerAssistant: loaded ✓" if sa else "ServerAssistant: NOT LOADED ✗"
            )
            await ctx.send(embed=emb)

    @levelrole.command(name="add")
    @commands.admin_or_permissions(manage_guild=True)
    async def levelrole_add(self, ctx: commands.Context, level: int, role: discord.Role):
        """Award a role when a member reaches this level (and above, if stack is on)."""
        if level < 1 or level > 500:
            await ctx.send("Level must be between **1** and **500**.")
            return
        if role.is_default() or role.managed:
            await ctx.send("Pick a normal assignable role (not @everyone or integration roles).")
            return
        rewards = await self.config.guild(ctx.guild).rewards()
        rewards[str(level)] = role.id
        await self.config.guild(ctx.guild).rewards.set(rewards)
        await ctx.send(f"At level **{level}**, members get {role.mention}.")

    @levelrole.command(name="remove")
    @commands.admin_or_permissions(manage_guild=True)
    async def levelrole_remove(self, ctx: commands.Context, level: int):
        """Remove a level reward."""
        rewards = await self.config.guild(ctx.guild).rewards()
        if str(level) not in rewards:
            await ctx.send("No reward at that level.")
            return
        del rewards[str(level)]
        await self.config.guild(ctx.guild).rewards.set(rewards)
        await ctx.send(f"Removed reward for level **{level}**.")

    @levelrole.command(name="list")
    async def levelrole_list(self, ctx: commands.Context):
        """List configured level rewards."""
        rewards = await self.config.guild(ctx.guild).rewards()
        if not rewards:
            await ctx.send("No level rewards yet. Admins: `levelrole add <level> @role`.")
            return
        lines = []
        for lvl in sorted(rewards.keys(), key=lambda x: int(x)):
            role = ctx.guild.get_role(int(rewards[lvl]))
            lines.append(f"**{lvl}** → {role.mention if role else '`missing role`'}")
        emb = Embed(title="Level rewards", description="\n".join(lines), color=0xF1C40F)
        emb.set_footer(text=f"Stack mode: {await self.config.guild(ctx.guild).stack()}")
        await ctx.send(embed=emb)

    @levelrole.command(name="sync")
    @commands.admin_or_permissions(manage_guild=True)
    async def levelrole_sync(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Re-apply level roles for a member (or yourself)."""
        if self._sa() is None:
            await ctx.send("Load **serverassistant** first — this cog reads XP from it.")
            return
        target = member or ctx.author
        await self.sync_roles(target, announce=False)
        lvl = await self._member_level(target)
        await ctx.send(f"Synced roles for {target.mention} (level **{lvl}**).")

    @levelrole.command(name="announce")
    @commands.admin_or_permissions(manage_guild=True)
    async def levelrole_announce(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ):
        """Set (or clear) the channel for level-role unlock announcements."""
        if channel is None:
            await self.config.guild(ctx.guild).announce_channel.set(None)
            await ctx.send("Level-role announcements cleared.")
            return
        await self.config.guild(ctx.guild).announce_channel.set(channel.id)
        await ctx.send(f"Unlock announcements → {channel.mention}")

    @levelrole.command(name="stack")
    @commands.admin_or_permissions(manage_guild=True)
    async def levelrole_stack(self, ctx: commands.Context, enabled: bool):
        """If true (default), keep all earned roles. If false, only the highest qualifying role stays."""
        await self.config.guild(ctx.guild).stack.set(enabled)
        await ctx.send(f"Stack mode: **{enabled}**")
