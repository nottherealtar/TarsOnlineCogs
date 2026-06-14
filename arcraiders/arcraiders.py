#
# Arc Raiders Map Rotation Tracker for Red-DiscordBot
# Live schedule: https://metaforge.app/arc-raiders/api
# Prefix-only commands — do not nest groups deeper than one level under ``arc``.
#

import asyncio
import logging
import re

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple

from .keys_data import (
    KEYS,
    MAP_INFO,
    RARITY_COLORS,
    RARITY_LABELS,
    get_key_by_id,
    list_key_names,
    search_keys,
)
from .metaforge import METAFORGE_ATTRIBUTION, MetaForgeSchedule

log = logging.getLogger("red.arcraiders")


class ArcRaiders(commands.Cog):
    """Arc Raiders map rotations, live event alerts, and key location lookup.

    Use ``[p]arc`` for the current rotation. Admins: ``[p]arc notify add`` then ``[p]arc notify enable``.
    """

    # Map display names and emojis
    MAPS = {
        "dam": {"name": "Dam", "emoji": "\U0001F4A7"},
        "buriedCity": {"name": "Buried City", "emoji": "\U0001F3DA"},
        "spaceport": {"name": "Spaceport", "emoji": "\U0001F680"},
        "blueGate": {"name": "Blue Gate", "emoji": "\U0001F535"},
        "stellaMontis": {"name": "Stella Montis", "emoji": "\u26F0\uFE0F"},
        "rivenTides": {"name": "Riven Tides", "emoji": "\U0001F30A"},
    }

    # Event types with emojis and descriptions
    EVENTS = {
        "None": {"emoji": "\u2796", "desc": "No active events", "major": False},
        "Harvester": {"emoji": "\U0001F69C", "desc": "Harvester active", "major": True},
        "Night": {"emoji": "\U0001F319", "desc": "Night time", "major": True},
        "Husks": {"emoji": "\U0001F47E", "desc": "Husks spawning", "major": True},
        "Blooms": {"emoji": "\U0001F338", "desc": "Blooms active", "major": True},
        "Storm": {"emoji": "\u26C8\uFE0F", "desc": "Storm incoming", "major": True},
        "Caches": {"emoji": "\U0001F4E6", "desc": "Caches available", "major": False},
        "Probes": {"emoji": "\U0001F6F0\uFE0F", "desc": "Probes detected", "major": False},
        "Tower": {"emoji": "\U0001F5FC", "desc": "Tower event", "major": True},
        "Bunker": {"emoji": "\U0001F3F0", "desc": "Bunker accessible", "major": True},
        "Matriarch": {"emoji": "\U0001F479", "desc": "Matriarch spawned", "major": True},
        "Cold": {"emoji": "\u2744\uFE0F", "desc": "Cold weather", "major": True},
        "Gate": {"emoji": "\U0001F6AA", "desc": "Gate event", "major": True},
        "Birds": {"emoji": "\U0001F426", "desc": "Birds active", "major": False},
        "Hurricane": {"emoji": "\U0001F32A\uFE0F", "desc": "Hurricane conditions", "major": True},
        "Beachcombing": {"emoji": "\U0001F3D6\uFE0F", "desc": "Beachcombing active", "major": False},
        "Close Scrutiny": {"emoji": "\U0001F50D", "desc": "Close Scrutiny event", "major": False},
    }

    # Fallback schedule when MetaForge is unreachable (UTC hour table)
    FALLBACK_ROTATIONS = [
        {"hour": 0, "dam": {"minor": "None", "major": "None"}, "buriedCity": {"minor": "Husks", "major": "None"}, "spaceport": {"minor": "None", "major": "Bunker"}, "blueGate": {"minor": "None", "major": "Cold"}, "stellaMontis": {"minor": "None", "major": "None"}},
        {"hour": 1, "dam": {"minor": "Caches", "major": "None"}, "buriedCity": {"minor": "None", "major": "Storm"}, "spaceport": {"minor": "Probes", "major": "None"}, "blueGate": {"minor": "None", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Harvester"}},
        {"hour": 2, "dam": {"minor": "None", "major": "Night"}, "buriedCity": {"minor": "None", "major": "None"}, "spaceport": {"minor": "None", "major": "Tower"}, "blueGate": {"minor": "Caches", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Blooms"}},
        {"hour": 3, "dam": {"minor": "None", "major": "Husks"}, "buriedCity": {"minor": "Probes", "major": "None"}, "spaceport": {"minor": "None", "major": "None"}, "blueGate": {"minor": "None", "major": "Matriarch"}, "stellaMontis": {"minor": "None", "major": "None"}},
        {"hour": 4, "dam": {"minor": "None", "major": "None"}, "buriedCity": {"minor": "None", "major": "Harvester"}, "spaceport": {"minor": "Caches", "major": "None"}, "blueGate": {"minor": "None", "major": "Night"}, "stellaMontis": {"minor": "Probes", "major": "None"}},
        {"hour": 5, "dam": {"minor": "Probes", "major": "None"}, "buriedCity": {"minor": "None", "major": "Blooms"}, "spaceport": {"minor": "None", "major": "Storm"}, "blueGate": {"minor": "None", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Bunker"}},
        {"hour": 6, "dam": {"minor": "None", "major": "Tower"}, "buriedCity": {"minor": "Caches", "major": "None"}, "spaceport": {"minor": "None", "major": "Matriarch"}, "blueGate": {"minor": "None", "major": "Husks"}, "stellaMontis": {"minor": "None", "major": "None"}},
        {"hour": 7, "dam": {"minor": "None", "major": "Storm"}, "buriedCity": {"minor": "None", "major": "Night"}, "spaceport": {"minor": "None", "major": "None"}, "blueGate": {"minor": "Probes", "major": "None"}, "stellaMontis": {"minor": "Caches", "major": "None"}},
        {"hour": 8, "dam": {"minor": "Caches", "major": "None"}, "buriedCity": {"minor": "None", "major": "Bunker"}, "spaceport": {"minor": "None", "major": "Harvester"}, "blueGate": {"minor": "None", "major": "Blooms"}, "stellaMontis": {"minor": "None", "major": "Cold"}},
        {"hour": 9, "dam": {"minor": "None", "major": "Matriarch"}, "buriedCity": {"minor": "None", "major": "None"}, "spaceport": {"minor": "Probes", "major": "None"}, "blueGate": {"minor": "None", "major": "Tower"}, "stellaMontis": {"minor": "None", "major": "Night"}},
        {"hour": 10, "dam": {"minor": "None", "major": "Blooms"}, "buriedCity": {"minor": "None", "major": "Cold"}, "spaceport": {"minor": "None", "major": "Husks"}, "blueGate": {"minor": "Caches", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Storm"}},
        {"hour": 11, "dam": {"minor": "None", "major": "None"}, "buriedCity": {"minor": "Probes", "major": "None"}, "spaceport": {"minor": "None", "major": "Night"}, "blueGate": {"minor": "None", "major": "Harvester"}, "stellaMontis": {"minor": "None", "major": "Matriarch"}},
        {"hour": 12, "dam": {"minor": "Probes", "major": "None"}, "buriedCity": {"minor": "None", "major": "Matriarch"}, "spaceport": {"minor": "Caches", "major": "None"}, "blueGate": {"minor": "None", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Tower"}},
        {"hour": 13, "dam": {"minor": "None", "major": "Harvester"}, "buriedCity": {"minor": "None", "major": "Tower"}, "spaceport": {"minor": "None", "major": "Cold"}, "blueGate": {"minor": "None", "major": "Storm"}, "stellaMontis": {"minor": "None", "major": "None"}},
        {"hour": 14, "dam": {"minor": "None", "major": "Bunker"}, "buriedCity": {"minor": "Caches", "major": "None"}, "spaceport": {"minor": "None", "major": "Blooms"}, "blueGate": {"minor": "None", "major": "Husks"}, "stellaMontis": {"minor": "Probes", "major": "None"}},
        {"hour": 15, "dam": {"minor": "None", "major": "Cold"}, "buriedCity": {"minor": "None", "major": "Husks"}, "spaceport": {"minor": "None", "major": "None"}, "blueGate": {"minor": "None", "major": "Bunker"}, "stellaMontis": {"minor": "Caches", "major": "None"}},
        {"hour": 16, "dam": {"minor": "Caches", "major": "None"}, "buriedCity": {"minor": "None", "major": "Blooms"}, "spaceport": {"minor": "None", "major": "Matriarch"}, "blueGate": {"minor": "None", "major": "Night"}, "stellaMontis": {"minor": "None", "major": "Harvester"}},
        {"hour": 17, "dam": {"minor": "None", "major": "Husks"}, "buriedCity": {"minor": "None", "major": "None"}, "spaceport": {"minor": "Probes", "major": "None"}, "blueGate": {"minor": "None", "major": "Tower"}, "stellaMontis": {"minor": "None", "major": "Storm"}},
        {"hour": 18, "dam": {"minor": "None", "major": "Night"}, "buriedCity": {"minor": "None", "major": "Storm"}, "spaceport": {"minor": "None", "major": "Harvester"}, "blueGate": {"minor": "Caches", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Blooms"}},
        {"hour": 19, "dam": {"minor": "None", "major": "Storm"}, "buriedCity": {"minor": "Probes", "major": "None"}, "spaceport": {"minor": "None", "major": "Tower"}, "blueGate": {"minor": "None", "major": "Matriarch"}, "stellaMontis": {"minor": "None", "major": "None"}},
        {"hour": 20, "dam": {"minor": "Probes", "major": "None"}, "buriedCity": {"minor": "None", "major": "Night"}, "spaceport": {"minor": "None", "major": "Bunker"}, "blueGate": {"minor": "None", "major": "Blooms"}, "stellaMontis": {"minor": "None", "major": "Cold"}},
        {"hour": 21, "dam": {"minor": "None", "major": "Tower"}, "buriedCity": {"minor": "None", "major": "Bunker"}, "spaceport": {"minor": "Caches", "major": "None"}, "blueGate": {"minor": "None", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Husks"}},
        {"hour": 22, "dam": {"minor": "None", "major": "Blooms"}, "buriedCity": {"minor": "Caches", "major": "None"}, "spaceport": {"minor": "None", "major": "Night"}, "blueGate": {"minor": "Probes", "major": "None"}, "stellaMontis": {"minor": "None", "major": "Matriarch"}},
        {"hour": 23, "dam": {"minor": "None", "major": "Matriarch"}, "buriedCity": {"minor": "None", "major": "Harvester"}, "spaceport": {"minor": "None", "major": "Storm"}, "blueGate": {"minor": "None", "major": "Cold"}, "stellaMontis": {"minor": "None", "major": "Bunker"}}
    ]

    def __init__(self, bot: Red):
        self.bot = bot
        self.schedule = MetaForgeSchedule()
        self.config = Config.get_conf(self, identifier=1357924680, force_registration=True)
        default_guild = {
            "auto_channel_id": None,
            "auto_message_id": None,
            "auto_enabled": False,
            "notify_enabled": False,
            "notify_channel_ids": [],
            "notify_maps": [],
            "notify_events": [],
            "notify_per_map": False,
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(last_notified_snapshot=None)
        self.update_task: Optional[asyncio.Task] = None
        self._last_rotation: Optional[dict] = None

    async def cog_load(self):
        """Start schedule sync and the auto-update task."""
        await self.schedule.start()
        await self.schedule.refresh(force=True)

        current = self._get_current_rotation()
        current_snapshot = self._rotation_snapshot(current)
        last_snapshot = await self.config.last_notified_snapshot()

        if last_snapshot and last_snapshot != current_snapshot:
            if await self._any_notify_enabled():
                previous = self._rotation_from_snapshot(last_snapshot, current.get("hour", 0))
                await self._send_change_notifications(previous, current)
            else:
                await self.config.last_notified_snapshot.set(current_snapshot)

        if not last_snapshot or last_snapshot == current_snapshot:
            await self.config.last_notified_snapshot.set(current_snapshot)
        self._last_rotation = current
        self.update_task = asyncio.create_task(self._auto_update_loop())

    async def cog_unload(self):
        """Cancel background tasks and close the API session."""
        if self.update_task:
            self.update_task.cancel()
        await self.schedule.close()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    async def red_delete_data_for_guild(self, *, guild_id: int, **kwargs):
        await self.config.guild_from_id(guild_id).clear()

    def _get_current_hour(self) -> int:
        """Get the current UTC hour."""
        return datetime.now(timezone.utc).hour

    def _using_live_data(self) -> bool:
        return self.schedule.has_live_data

    def _data_footer(self, extra: str = "") -> str:
        if self._using_live_data():
            base = METAFORGE_ATTRIBUTION
        else:
            base = "Fallback schedule — MetaForge API unavailable"
        return f"{extra} | {base}" if extra else base

    def _rotation_snapshot(self, rotation: dict) -> Dict[str, List[str]]:
        return {
            map_key: [
                rotation.get(map_key, {}).get("minor", "None"),
                rotation.get(map_key, {}).get("major", "None"),
            ]
            for map_key in self.MAPS
        }

    def _rotation_from_snapshot(self, snapshot: Dict[str, List[str]], hour: int) -> dict:
        rotation = {"hour": hour}
        for map_key in self.MAPS:
            minor, major = snapshot.get(map_key, ["None", "None"])
            rotation[map_key] = {"minor": minor, "major": major}
        return rotation

    def _get_fallback_rotation(self, hour: int) -> dict:
        return self.FALLBACK_ROTATIONS[hour % 24]

    def _get_rotation(self, hour: int) -> dict:
        """Get rotation data for a UTC hour (live schedule or fallback table)."""
        if self._using_live_data():
            now = datetime.now(timezone.utc)
            when = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            return self.schedule.build_rotation(when, hour_label=hour, map_keys=list(self.MAPS.keys()))
        return self._get_fallback_rotation(hour)

    def _get_current_rotation(self) -> dict:
        if self._using_live_data():
            return self.schedule.build_rotation(map_keys=list(self.MAPS.keys()))
        return self._get_fallback_rotation(self._get_current_hour())

    def _get_next_rotation(self) -> Tuple[dict, int]:
        if self._using_live_data():
            minutes = self.schedule.minutes_until_next_change()
            next_when = self.schedule.next_change_at()
            return (
                self.schedule.build_rotation(next_when, map_keys=list(self.MAPS.keys())),
                minutes,
            )

        now = datetime.now(timezone.utc)
        next_hour = (now.hour + 1) % 24
        minutes_until = 60 - now.minute
        return self._get_fallback_rotation(next_hour), minutes_until

    def _format_event(self, event_name: str, is_major: bool = False) -> str:
        """Format an event with emoji."""
        event = self.EVENTS.get(event_name, {"emoji": "\u2753", "desc": "Unknown"})
        multiplier = " (2x)" if is_major and event_name != "None" else ""
        return f"{event['emoji']} {event_name}{multiplier}"

    def _get_map_status(self, rotation: dict, map_key: str) -> str:
        """Get the status string for a specific map."""
        map_data = rotation.get(map_key, {"minor": "None", "major": "None"})
        minor = map_data.get("minor", "None")
        major = map_data.get("major", "None")

        parts = []
        if major != "None":
            parts.append(self._format_event(major, is_major=True))
        if minor != "None":
            parts.append(self._format_event(minor, is_major=False))
        if not parts:
            parts.append(self._format_event("None"))

        return " | ".join(parts)

    def _build_rotation_embed(self, rotation: dict, title: str, color: int = 0x7B68EE) -> discord.Embed:
        """Build an embed showing all map rotations."""
        embed = discord.Embed(title=title, color=color)

        for map_key, map_info in self.MAPS.items():
            status = self._get_map_status(rotation, map_key)
            embed.add_field(
                name=f"{map_info['emoji']} {map_info['name']}",
                value=status,
                inline=False
            )

        embed.set_footer(text=self._data_footer(f"Hour {rotation['hour']}:00 UTC"))
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    def _build_overview_embed(self) -> discord.Embed:
        """Build an overview embed with current and next rotation."""
        current = self._get_current_rotation()
        next_rot, minutes = self._get_next_rotation()
        now = datetime.now(timezone.utc)

        if self._using_live_data():
            description = f"**Next rotation change in:** {minutes} minutes"
            next_label = next_rot.get("hour")
            if isinstance(next_label, int):
                next_heading = f"\U0001F7E2 Next Rotation (~{next_label:02d}:00 UTC)"
            else:
                next_heading = "\U0001F7E2 Next Rotation"
        else:
            description = (
                f"**Current Hour:** {current['hour']}:00 UTC\n"
                f"**Next rotation in:** {minutes} minutes"
            )
            next_heading = f"\U0001F7E2 Next Hour ({next_rot['hour']}:00 UTC)"

        embed = discord.Embed(
            title="\U0001F3AE Arc Raiders Map Rotation",
            description=description,
            color=0x7B68EE,
        )

        # Current conditions
        current_text = ""
        for map_key, map_info in self.MAPS.items():
            status = self._get_map_status(current, map_key)
            current_text += f"{map_info['emoji']} **{map_info['name']}:** {status}\n"

        embed.add_field(name="\U0001F534 Current Conditions", value=current_text, inline=False)

        # Next conditions
        next_text = ""
        for map_key, map_info in self.MAPS.items():
            status = self._get_map_status(next_rot, map_key)
            next_text += f"{map_info['emoji']} **{map_info['name']}:** {status}\n"

        embed.add_field(name=next_heading, value=next_text, inline=False)

        embed.set_footer(text=self._data_footer(now.strftime("Updated %H:%M UTC")))
        embed.timestamp = now
        return embed

    def _resolve_map_key(self, map_name: str) -> Optional[str]:
        """Resolve a user-provided map name to an internal map key."""
        search = map_name.lower().replace(" ", "").replace("_", "")
        for key, info in self.MAPS.items():
            if search in key.lower() or search in info["name"].lower().replace(" ", ""):
                return key
        return None

    def _resolve_text_channel(
        self, ctx: commands.Context, channel_text: Optional[str] = None
    ) -> Optional[discord.TextChannel]:
        """Resolve a channel from mention, name, or default to the current channel."""
        if not channel_text or channel_text.lower() in ("here", "this"):
            return ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None

        mention = re.fullmatch(r"<#(\d+)>", channel_text.strip())
        if mention:
            channel = ctx.guild.get_channel(int(mention.group(1)))
            if isinstance(channel, discord.TextChannel):
                return channel

        cleaned = channel_text.strip().lstrip("#").strip()
        if not cleaned:
            return ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None

        if cleaned.isdigit():
            channel = ctx.guild.get_channel(int(cleaned))
            if isinstance(channel, discord.TextChannel):
                return channel

        channel = discord.utils.get(ctx.guild.text_channels, name=cleaned)
        if channel:
            return channel

        for channel in ctx.guild.text_channels:
            if cleaned.lower() in channel.name.lower():
                return channel

        return None

    def _map_events(self, rotation: dict, map_key: str) -> Tuple[str, str]:
        map_data = rotation.get(map_key, {"minor": "None", "major": "None"})
        return map_data.get("minor", "None"), map_data.get("major", "None")

    def _map_changed(self, previous: dict, current: dict, map_key: str) -> bool:
        prev_minor, prev_major = self._map_events(previous, map_key)
        curr_minor, curr_major = self._map_events(current, map_key)
        return prev_minor != curr_minor or prev_major != curr_major

    def _changed_maps(
        self, previous: dict, current: dict, allowed_maps: Optional[Set[str]] = None
    ) -> List[str]:
        changed = []
        for map_key in self.MAPS:
            if allowed_maps and map_key not in allowed_maps:
                continue
            if self._map_changed(previous, current, map_key):
                changed.append(map_key)
        return changed

    def _events_in_change(
        self, previous: dict, current: dict, map_key: str
    ) -> Set[str]:
        prev_minor, prev_major = self._map_events(previous, map_key)
        curr_minor, curr_major = self._map_events(current, map_key)
        events = {prev_minor, prev_major, curr_minor, curr_major}
        events.discard("None")
        return events

    def _passes_event_filter(
        self, previous: dict, current: dict, map_key: str, notify_events: List[str]
    ) -> bool:
        if not notify_events:
            return True
        changed_events = self._events_in_change(previous, current, map_key)
        filter_set = {event.lower() for event in notify_events}
        return any(event.lower() in filter_set for event in changed_events)

    def _build_map_change_embed(
        self, map_key: str, previous: dict, current: dict, when: datetime
    ) -> discord.Embed:
        map_info = self.MAPS[map_key]
        prev_status = self._get_map_status(previous, map_key)
        curr_status = self._get_map_status(current, map_key)

        embed = discord.Embed(
            title=f"\U0001F504 {map_info['emoji']} {map_info['name']} — Rotation Changed",
            description=(
                f"**{when.strftime('%H:%M UTC')}**\n\n"
                f"**Before:** {prev_status}\n"
                f"**Now:** {curr_status}"
            ),
            color=0xFF6B35,
        )
        embed.set_footer(text=self._data_footer("Arc Raiders map rotation update"))
        embed.timestamp = when
        return embed

    def _build_rotation_change_embed(
        self, changed_map_keys: List[str], previous: dict, current: dict, when: datetime
    ) -> discord.Embed:
        embed = discord.Embed(
            title="\U0001F504 Arc Raiders Map Rotation Update",
            description=f"**{when.strftime('%H:%M UTC')}** — the following maps changed:",
            color=0xFF6B35,
        )
        for map_key in changed_map_keys:
            map_info = self.MAPS[map_key]
            prev_status = self._get_map_status(previous, map_key)
            curr_status = self._get_map_status(current, map_key)
            embed.add_field(
                name=f"{map_info['emoji']} {map_info['name']}",
                value=f"**Before:** {prev_status}\n**Now:** {curr_status}",
                inline=False,
            )
        embed.set_footer(text=self._data_footer("Arc Raiders rotation alert"))
        embed.timestamp = when
        return embed

    def _build_key_embed(self, key: dict, *, disambiguate: bool = False) -> discord.Embed:
        map_data = MAP_INFO[key["map"]]
        rarity = key.get("rarity", "uncommon")
        color = RARITY_COLORS.get(rarity, 0x7B68EE)

        title = f"\U0001F511 {key['name']}"
        if disambiguate:
            title = f"\U0001F511 {key['name']} ({map_data['name']})"

        embed = discord.Embed(
            title=title,
            description=key.get("description", ""),
            color=color,
        )
        embed.add_field(name="Map", value=map_data["name"], inline=True)
        embed.add_field(name="Rarity", value=RARITY_LABELS.get(rarity, rarity.title()), inline=True)

        location = key.get("location", "Unknown")
        if key.get("level"):
            location = f"{location} ({key['level'].title()} level)"
        embed.add_field(name="Location", value=location, inline=False)

        instructions = key.get("instructions")
        if instructions:
            if len(instructions) > 1000:
                instructions = instructions[:997] + "..."
            embed.add_field(name="How to Open", value=instructions, inline=False)

        image = key.get("door_image") or map_data.get("preview")
        if image:
            embed.set_image(url=image)

        embed.set_footer(text="Arc Raiders key lookup")
        return embed

    async def _reply_key_lookup(self, ctx: commands.Context, key_name: str):
        direct = get_key_by_id(key_name)
        if direct:
            await ctx.send(embed=self._build_key_embed(direct))
            return

        matches = search_keys(key_name)
        if not matches:
            sample = ", ".join(list_key_names()[:8])
            await ctx.send(
                f"No key found for **{key_name}**. Try `control tower dam`, "
                f"`town hall`, or `raider hatch spaceport`.\nExamples: {sample}…"
            )
            return

        disambiguate = len({key["name"] for key in matches}) < len(matches) or len(matches) > 1

        if len(matches) == 1:
            await ctx.send(embed=self._build_key_embed(matches[0], disambiguate=disambiguate))
            return

        if len(matches) <= 4:
            for key in matches:
                await ctx.send(embed=self._build_key_embed(key, disambiguate=True))
            return

        lines = []
        for key in matches[:15]:
            map_name = MAP_INFO[key["map"]]["name"]
            lines.append(f"• **{key['name']}** — {map_name} ({key.get('location', 'Unknown')})")
        embed = discord.Embed(
            title=f"\U0001F511 Key matches for \"{key_name}\"",
            description="\n".join(lines),
            color=0x7B68EE,
        )
        embed.set_footer(text="Add a map name, e.g. arc key control tower dam")
        await ctx.send(embed=embed)

    async def _update_auto_embeds(self):
        """Refresh pinned/live rotation embeds in configured guild channels."""
        all_guilds = await self.config.all_guilds()
        for guild_id, settings in all_guilds.items():
            if not settings.get("auto_enabled"):
                continue

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            channel = guild.get_channel(settings.get("auto_channel_id"))
            if not channel:
                continue

            message_id = settings.get("auto_message_id")

            try:
                embed = self._build_overview_embed()

                if message_id:
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.edit(embed=embed)
                    except discord.NotFound:
                        msg = await channel.send(embed=embed)
                        await self.config.guild(guild).auto_message_id.set(msg.id)
                else:
                    msg = await channel.send(embed=embed)
                    await self.config.guild(guild).auto_message_id.set(msg.id)

            except (discord.Forbidden, discord.HTTPException):
                pass

    async def _send_change_notifications(self, previous: dict, current: dict):
        """Post rotation change alerts to configured notification channels."""
        when = datetime.now(timezone.utc)
        all_guilds = await self.config.all_guilds()

        for guild_id, settings in all_guilds.items():
            if not settings.get("notify_enabled"):
                continue

            channel_ids = settings.get("notify_channel_ids") or []
            if not channel_ids:
                continue

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            allowed_maps = None
            notify_maps = settings.get("notify_maps") or []
            if notify_maps:
                allowed_maps = set()
                for map_name in notify_maps:
                    resolved = self._resolve_map_key(map_name)
                    if resolved:
                        allowed_maps.add(resolved)

            notify_events = settings.get("notify_events") or []
            changed = self._changed_maps(previous, current, allowed_maps)
            if notify_events:
                changed = [
                    map_key
                    for map_key in changed
                    if self._passes_event_filter(previous, current, map_key, notify_events)
                ]

            if not changed:
                continue

            per_map = settings.get("notify_per_map", False)
            if per_map:
                embeds = [
                    self._build_map_change_embed(map_key, previous, current, when)
                    for map_key in changed
                ]
            else:
                embeds = [self._build_rotation_change_embed(changed, previous, current, when)]

            for channel_id in channel_ids:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                try:
                    for embed in embeds:
                        await channel.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException):
                    pass

        await self.config.last_notified_snapshot.set(self._rotation_snapshot(current))

    async def _any_notify_enabled(self) -> bool:
        for settings in (await self.config.all_guilds()).values():
            if settings.get("notify_enabled") and settings.get("notify_channel_ids"):
                return True
        return False

    @commands.group(name="arc", invoke_without_command=True)
    @commands.guild_only()
    async def arc(self, ctx: commands.Context):
        """Arc Raiders map rotation overview."""
        embed = self._build_overview_embed()
        await ctx.send(embed=embed)

    @arc.command(name="help")
    async def arc_help(self, ctx: commands.Context):
        """List Arc Raiders commands."""
        p = ctx.clean_prefix
        embed = discord.Embed(title="Arc Raiders Commands", color=0x7B68EE)
        embed.description = (
            f"**Rotation**\n"
            f"`{p}arc` — current overview\n"
            f"`{p}arc now` · `{p}arc next` · `{p}arc hour <0-23>`\n"
            f"`{p}arc map <name>` · `{p}arc event <name>`\n"
            f"`{p}arc maps` · `{p}arc events` · `{p}arc status`\n\n"
            f"**Keys**\n"
            f"`{p}arc key <name>` — door location + directions\n"
            f"`{p}arc keys [map]` — list keys\n\n"
            f"**Admin (Manage Server)**\n"
            f"`{p}arc auto channel` · `{p}arc auto enable`\n"
            f"`{p}arc notify add` · `{p}arc notify enable` · `{p}arc notify test`"
        )
        embed.set_footer(text=self._data_footer())
        await ctx.send(embed=embed)

    @arc.command(name="now")
    async def arc_now(self, ctx: commands.Context):
        """Show current map conditions."""
        rotation = self._get_current_rotation()
        embed = self._build_rotation_embed(
            rotation,
            f"\U0001F534 Current Map Conditions (Hour {rotation['hour']}:00 UTC)",
            color=0xFF4500
        )
        await ctx.send(embed=embed)

    @arc.command(name="next")
    async def arc_next(self, ctx: commands.Context):
        """Show next hour's map conditions."""
        rotation, minutes = self._get_next_rotation()
        embed = self._build_rotation_embed(
            rotation,
            f"\U0001F7E2 Next Rotation (Hour {rotation['hour']}:00 UTC) - in {minutes} min",
            color=0x32CD32
        )
        await ctx.send(embed=embed)

    @arc.command(name="hour")
    async def arc_hour(self, ctx: commands.Context, hour: int):
        """Show map conditions for a specific UTC hour (0-23)."""
        if hour < 0 or hour > 23:
            await ctx.send("Hour must be between 0 and 23.")
            return
        rotation = self._get_rotation(hour)
        embed = self._build_rotation_embed(
            rotation,
            f"\U0001F550 Map Conditions at {hour:02d}:00 UTC",
            color=0x4169E1
        )
        await ctx.send(embed=embed)

    @arc.command(name="map")
    async def arc_map(self, ctx: commands.Context, *, map_name: str):
        """Show 24-hour schedule for a specific map."""
        # Find the map
        map_key = None
        map_info = None
        search = map_name.lower().replace(" ", "")

        for key, info in self.MAPS.items():
            if search in key.lower() or search in info["name"].lower().replace(" ", ""):
                map_key = key
                map_info = info
                break

        if not map_key:
            map_list = ", ".join([info["name"] for info in self.MAPS.values()])
            await ctx.send(f"Map not found. Available maps: {map_list}")
            return

        embed = discord.Embed(
            title=f"{map_info['emoji']} {map_info['name']} - Upcoming Schedule",
            color=0x7B68EE,
        )

        now = datetime.now(timezone.utc)
        schedule_text = ""

        if self._using_live_data():
            timeline = self.schedule.map_timeline(map_key)
            if not timeline:
                schedule_text = "*No upcoming events in the live schedule.*"
            for slot in timeline:
                indicator = "\U0001F534" if slot["active_now"] else "\u26AA"
                schedule_text += (
                    f"{indicator} **{slot['start'].strftime('%H:%M UTC')}** - "
                    f"{self._format_event(slot['name'], is_major=slot['major'])}\n"
                )
                if len(schedule_text) > 900:
                    embed.add_field(name="\u200b", value=schedule_text, inline=False)
                    schedule_text = ""
        else:
            current_hour = self._get_current_hour()
            for rotation in self.FALLBACK_ROTATIONS:
                hour = rotation["hour"]
                status = self._get_map_status(rotation, map_key)
                indicator = "\U0001F534" if hour == current_hour else "\u26AA"
                schedule_text += f"{indicator} **{hour:02d}:00** - {status}\n"
                if len(schedule_text) > 900:
                    embed.add_field(name="\u200b", value=schedule_text, inline=False)
                    schedule_text = ""

        if schedule_text:
            embed.add_field(name="\u200b", value=schedule_text, inline=False)

        embed.set_footer(text=self._data_footer(f"\U0001F534 = active now | {now.strftime('%H:%M UTC')}"))
        await ctx.send(embed=embed)

    @arc.command(name="event")
    async def arc_event(self, ctx: commands.Context, *, event_name: str):
        """Find when a specific event occurs across all maps."""
        event_key = None
        for key in self.EVENTS.keys():
            if event_name.lower() == key.lower() or event_name.lower() in key.lower():
                event_key = key
                break

        if not event_key or event_key == "None":
            event_list = ", ".join([k for k in self.EVENTS.keys() if k != "None"])
            await ctx.send(f"Event not found. Available events: {event_list}")
            return

        event_info = self.EVENTS[event_key]
        embed = discord.Embed(
            title=f"{event_info['emoji']} {event_key} Schedule",
            description=event_info["desc"],
            color=0xFF6B6B if event_info["major"] else 0x6BCB77,
        )

        found_any = False
        now = datetime.now(timezone.utc)

        if self._using_live_data():
            occurrences = self.schedule.find_event_occurrences(event_key)
            by_map: Dict[str, List[str]] = {}
            for row in occurrences:
                if row["start"] < now:
                    continue
                if row["start"] > now + timedelta(hours=24):
                    continue
                label = (
                    f"{row['start'].strftime('%H:%M UTC')} — "
                    f"{self._format_event(row['name'], is_major=row['major'])}"
                )
                if row["active_now"]:
                    label += " \U0001F534"
                by_map.setdefault(row["map_key"], []).append(label)

            for map_key, map_info in self.MAPS.items():
                slots = by_map.get(map_key)
                if slots:
                    found_any = True
                    embed.add_field(
                        name=f"{map_info['emoji']} {map_info['name']}",
                        value=", ".join(slots[:12]),
                        inline=False,
                    )
        else:
            current_hour = self._get_current_hour()
            for map_key, map_info in self.MAPS.items():
                hits = []
                for rotation in self.FALLBACK_ROTATIONS:
                    map_data = rotation.get(map_key, {})
                    hour = rotation["hour"]
                    if map_data.get("major") == event_key:
                        indicator = "\U0001F534" if hour == current_hour else ""
                        hits.append(f"{hour:02d}:00 (2x){indicator}")
                    elif map_data.get("minor") == event_key:
                        indicator = "\U0001F534" if hour == current_hour else ""
                        hits.append(f"{hour:02d}:00{indicator}")

                if hits:
                    found_any = True
                    embed.add_field(
                        name=f"{map_info['emoji']} {map_info['name']}",
                        value=", ".join(hits),
                        inline=False,
                    )

        if not found_any:
            embed.description += "\n\n*This event is not scheduled in the next 24 hours.*"

        embed.set_footer(text=self._data_footer(now.strftime("\U0001F534 = active now | %H:%M UTC")))
        await ctx.send(embed=embed)

    @arc.command(name="status")
    async def arc_status(self, ctx: commands.Context):
        """Show whether live MetaForge schedule data is being used."""
        await self.schedule.refresh()
        if self._using_live_data():
            minutes = self.schedule.minutes_until_next_change()
            await ctx.send(
                f"\U0001F7E2 **Live schedule active** — next change in ~{minutes} min.\n"
                f"{METAFORGE_ATTRIBUTION}"
            )
        else:
            error = self.schedule.last_error or "unknown error"
            await ctx.send(
                f"\U0001F7E1 **Using fallback schedule** — could not reach MetaForge ({error}).\n"
                "Rotation commands still work from the cached UTC table."
            )

    @arc.command(name="events")
    async def arc_events(self, ctx: commands.Context):
        """List all event types."""
        embed = discord.Embed(
            title="\U0001F4CB Arc Raiders Events",
            color=0x7B68EE
        )

        major_events = []
        minor_events = []

        for name, info in self.EVENTS.items():
            if name == "None":
                continue
            entry = f"{info['emoji']} **{name}** - {info['desc']}"
            if info["major"]:
                major_events.append(entry)
            else:
                minor_events.append(entry)

        embed.add_field(
            name="\U0001F525 Major Events (2x Multiplier)",
            value="\n".join(major_events) if major_events else "None",
            inline=False
        )
        embed.add_field(
            name="\U0001F4A0 Minor Events",
            value="\n".join(minor_events) if minor_events else "None",
            inline=False
        )

        await ctx.send(embed=embed)

    @arc.command(name="maps")
    async def arc_maps(self, ctx: commands.Context):
        """List all available maps."""
        embed = discord.Embed(
            title="\U0001F5FA\uFE0F Arc Raiders Maps",
            color=0x7B68EE
        )

        map_list = "\n".join([
            f"{info['emoji']} **{info['name']}**"
            for info in self.MAPS.values()
        ])

        embed.description = map_list
        embed.set_footer(text=f"Use [p]arc map <name> to see a map's 24-hour schedule")
        await ctx.send(embed=embed)

    @arc.command(name="key")
    async def arc_key(self, ctx: commands.Context, *, key_name: str):
        """Look up where to use a key. Shows a map/door image and directions."""
        await self._reply_key_lookup(ctx, key_name)

    @arc.command(name="keys")
    async def arc_keys(self, ctx: commands.Context, *, map_name: Optional[str] = None):
        """List all known keys, optionally filtered by map."""
        map_filter = None
        if map_name:
            map_filter = self._resolve_map_key(map_name)
            if not map_filter:
                map_list = ", ".join(info["name"] for info in self.MAPS.values())
                await ctx.send(f"Map not found. Available maps: {map_list}")
                return

        embed = discord.Embed(title="\U0001F511 Arc Raiders Keys", color=0x7B68EE)
        for map_id, map_data in MAP_INFO.items():
            if map_filter and map_id != map_filter:
                continue
            map_keys = [k for k in KEYS if k["map"] == map_id]
            if not map_keys:
                continue
            entries = []
            seen = set()
            for key in map_keys:
                label = key["name"]
                if label in seen:
                    continue
                seen.add(label)
                rarity = RARITY_LABELS.get(key.get("rarity", ""), "")
                entries.append(f"**{label}** ({rarity})" if rarity else f"**{label}**")
            embed.add_field(
                name=map_data["name"],
                value="\n".join(entries) if entries else "None",
                inline=False,
            )

        embed.set_footer(text="Use [p]arc key <name> for location images and directions")
        await ctx.send(embed=embed)

    # Auto-update functionality
    @arc.group(name="auto", invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_auto(self, ctx: commands.Context):
        """Configure automatic rotation updates."""
        settings = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(settings["auto_channel_id"]) if settings["auto_channel_id"] else None

        embed = discord.Embed(title="Arc Raiders Auto-Update Settings", color=0x7B68EE)
        embed.add_field(name="Enabled", value="Yes" if settings["auto_enabled"] else "No", inline=True)
        embed.add_field(name="Channel", value=channel.mention if channel else "Not set", inline=True)
        embed.set_footer(text="Use subcommands: enable, disable, channel")
        await ctx.send(embed=embed)

    @arc_auto.command(name="channel")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_auto_channel(self, ctx: commands.Context, *, channel: Optional[str] = None):
        """Set the channel for automatic rotation updates (defaults to this channel)."""
        resolved = self._resolve_text_channel(ctx, channel)
        if not resolved:
            await ctx.send("Could not find that channel. Use `#channel-name`, a mention, or run this in the target channel.")
            return
        await self.config.guild(ctx.guild).auto_channel_id.set(resolved.id)
        await ctx.send(f"Auto-update channel set to {resolved.mention}.")

    @arc_auto.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_auto_enable(self, ctx: commands.Context):
        """Enable automatic rotation updates."""
        channel_id = await self.config.guild(ctx.guild).auto_channel_id()
        if not channel_id:
            await ctx.send("Please set a channel first with `arc auto channel #channel`.")
            return
        await self.config.guild(ctx.guild).auto_enabled.set(True)
        await ctx.send("Auto-updates enabled. The live rotation embed will refresh when events change.")

        # Post initial message
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            embed = self._build_overview_embed()
            msg = await channel.send(embed=embed)
            await self.config.guild(ctx.guild).auto_message_id.set(msg.id)

    @arc_auto.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_auto_disable(self, ctx: commands.Context):
        """Disable automatic rotation updates."""
        await self.config.guild(ctx.guild).auto_enabled.set(False)
        await ctx.send("Auto-updates disabled.")

    @arc.group(name="notify", invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify(self, ctx: commands.Context):
        """Configure automatic posts when map rotations change."""
        settings = await self.config.guild(ctx.guild).all()
        channels = []
        for channel_id in settings.get("notify_channel_ids") or []:
            channel = ctx.guild.get_channel(channel_id)
            channels.append(channel.mention if channel else f"`{channel_id}` (missing)")

        notify_maps = settings.get("notify_maps") or []
        notify_events = settings.get("notify_events") or []

        embed = discord.Embed(title="Arc Raiders Rotation Notifications", color=0x7B68EE)
        embed.add_field(
            name="Enabled",
            value="Yes" if settings.get("notify_enabled") else "No",
            inline=True,
        )
        embed.add_field(
            name="Post style",
            value="One message per map" if settings.get("notify_per_map") else "Single summary message",
            inline=True,
        )
        embed.add_field(
            name="Channels",
            value="\n".join(channels) if channels else "None — use `arc notify add` in a channel",
            inline=False,
        )
        embed.add_field(
            name="Map filter",
            value=", ".join(notify_maps) if notify_maps else "All maps",
            inline=False,
        )
        embed.add_field(
            name="Event filter",
            value=", ".join(notify_events) if notify_events else "Any change",
            inline=False,
        )
        embed.set_footer(text="Posts when live map events change (MetaForge schedule)")
        await ctx.send(embed=embed)

    @arc_notify.command(name="add", aliases=["addchannel"])
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_add(self, ctx: commands.Context, *, channel: Optional[str] = None):
        """Add a channel for rotation change alerts (defaults to this channel)."""
        resolved = self._resolve_text_channel(ctx, channel)
        if not resolved:
            await ctx.send(
                "Could not find that channel. Try:\n"
                "• `arc notify add` — while in the target channel\n"
                "• `arc notify add #arc-raiders-events` — no space after `#`"
            )
            return
        channel_ids = await self.config.guild(ctx.guild).notify_channel_ids()
        if resolved.id in channel_ids:
            await ctx.send(f"{resolved.mention} is already a notification channel.")
            return
        channel_ids.append(resolved.id)
        await self.config.guild(ctx.guild).notify_channel_ids.set(channel_ids)
        await ctx.send(f"Added {resolved.mention} for rotation alerts.")

    @arc_notify.command(name="remove", aliases=["removechannel", "del", "delete"])
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_remove(self, ctx: commands.Context, *, channel: Optional[str] = None):
        """Remove a notification channel (defaults to this channel)."""
        resolved = self._resolve_text_channel(ctx, channel)
        if not resolved:
            await ctx.send("Could not find that channel.")
            return
        channel_ids = await self.config.guild(ctx.guild).notify_channel_ids()
        if resolved.id not in channel_ids:
            await ctx.send(f"{resolved.mention} is not configured.")
            return
        channel_ids.remove(resolved.id)
        await self.config.guild(ctx.guild).notify_channel_ids.set(channel_ids)
        await ctx.send(f"Removed {resolved.mention} from rotation alerts.")

    @arc_notify.command(name="channels", aliases=["list", "listchannels"])
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_channels(self, ctx: commands.Context):
        """List configured notification channels."""
        channel_ids = await self.config.guild(ctx.guild).notify_channel_ids()
        if not channel_ids:
            await ctx.send("No notification channels configured.")
            return
        lines = []
        for channel_id in channel_ids:
            channel = ctx.guild.get_channel(channel_id)
            lines.append(channel.mention if channel else f"`{channel_id}` (missing)")
        await ctx.send("**Notification channels:**\n" + "\n".join(lines))

    @arc_notify.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_enable(self, ctx: commands.Context):
        """Enable automatic rotation change posts."""
        channel_ids = await self.config.guild(ctx.guild).notify_channel_ids()
        if not channel_ids:
            await ctx.send("Add at least one channel with `arc notify add` first.")
            return
        await self.config.guild(ctx.guild).notify_enabled.set(True)
        await ctx.send(
            "Rotation notifications enabled. The bot will post when live map events change."
        )

    @arc_notify.command(name="disable")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_disable(self, ctx: commands.Context):
        """Disable automatic rotation change posts."""
        await self.config.guild(ctx.guild).notify_enabled.set(False)
        await ctx.send("Rotation notifications disabled.")

    @arc_notify.command(name="maps")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_maps(self, ctx: commands.Context, *map_names: str):
        """Set which maps to watch (leave empty for all maps)."""
        if not map_names or map_names[0].lower() in ("all", "clear", "reset"):
            await self.config.guild(ctx.guild).notify_maps.set([])
            await ctx.send("Map filter cleared — all maps will trigger notifications.")
            return

        invalid = []
        valid = []
        for name in map_names:
            if self._resolve_map_key(name):
                valid.append(name)
            else:
                invalid.append(name)

        if invalid:
            map_list = ", ".join(info["name"] for info in self.MAPS.values())
            await ctx.send(f"Unknown map(s): {', '.join(invalid)}. Available: {map_list}")
            return

        await self.config.guild(ctx.guild).notify_maps.set(valid)
        await ctx.send(f"Notifications limited to: {', '.join(valid)}")

    @arc_notify.command(name="events")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_events(self, ctx: commands.Context, *event_names: str):
        """Set which events trigger alerts (leave empty for any change)."""
        if not event_names or event_names[0].lower() in ("all", "clear", "reset"):
            await self.config.guild(ctx.guild).notify_events.set([])
            await ctx.send("Event filter cleared — any rotation change will notify.")
            return

        invalid = []
        valid = []
        for name in event_names:
            matched = None
            for key in self.EVENTS:
                if name.lower() == key.lower():
                    matched = key
                    break
            if matched:
                valid.append(matched)
            else:
                invalid.append(name)

        if invalid:
            event_list = ", ".join(k for k in self.EVENTS if k != "None")
            await ctx.send(f"Unknown event(s): {', '.join(invalid)}. Available: {event_list}")
            return

        await self.config.guild(ctx.guild).notify_events.set(valid)
        await ctx.send(f"Notifications limited to events involving: {', '.join(valid)}")

    @arc_notify.command(name="style")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_style(self, ctx: commands.Context, style: str):
        """Set post style: `summary` (one message) or `permap` (one message per map)."""
        style = style.lower()
        if style in ("summary", "single", "one"):
            await self.config.guild(ctx.guild).notify_per_map.set(False)
            await ctx.send("Notification style set to a single summary message.")
        elif style in ("permap", "per", "map", "separate"):
            await self.config.guild(ctx.guild).notify_per_map.set(True)
            await ctx.send("Notification style set to one message per changed map.")
        else:
            await ctx.send("Use `summary` or `permap`.")

    @arc_notify.command(name="test")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_notify_test(self, ctx: commands.Context):
        """Preview what a rotation alert looks like in this channel."""
        await self.schedule.refresh()
        current = self._get_current_rotation()
        previous = self._last_rotation or current
        changed = self._changed_maps(previous, current)
        if not changed:
            changed = list(self.MAPS.keys())[:2]

        embed = self._build_rotation_change_embed(
            changed, previous, current, datetime.now(timezone.utc)
        )
        embed.title = "\U0001F9EA Test — Arc Raiders Rotation Notification"
        await ctx.send(embed=embed)

    async def _auto_update_loop(self):
        """Poll MetaForge and post alerts when live map events change."""
        await self.bot.wait_until_ready()

        while True:
            try:
                await self.schedule.refresh()
                current = self._get_current_rotation()
                snapshot = self._rotation_snapshot(current)
                last_snapshot = await self.config.last_notified_snapshot()

                await self._update_auto_embeds()

                if last_snapshot != snapshot:
                    if last_snapshot:
                        previous = self._rotation_from_snapshot(
                            last_snapshot, current.get("hour", self._get_current_hour())
                        )
                        await self._send_change_notifications(previous, current)
                    else:
                        await self.config.last_notified_snapshot.set(snapshot)
                    self._last_rotation = current

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.exception("Arc Raiders update loop error: %s", exc)
                await asyncio.sleep(60)
