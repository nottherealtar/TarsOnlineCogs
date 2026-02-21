#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#
# Arc Raiders Map Rotation Tracker for Red-DiscordBot
# Based on: https://github.com/zfael/arc-raiders-discord-bot

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio


class ArcRaiders(commands.Cog):
    """Track Arc Raiders map rotations and events."""

    # Map display names and emojis
    MAPS = {
        "dam": {"name": "Dam", "emoji": "\U0001F4A7"},
        "buriedCity": {"name": "Buried City", "emoji": "\U0001F3DA"},
        "spaceport": {"name": "Spaceport", "emoji": "\U0001F680"},
        "blueGate": {"name": "Blue Gate", "emoji": "\U0001F535"},
        "stellaMontis": {"name": "Stella Montis", "emoji": "\u26F0\uFE0F"}
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
        "Birds": {"emoji": "\U0001F426", "desc": "Birds active", "major": False}
    }

    # 24-hour rotation schedule (UTC-based)
    MAP_ROTATIONS = [
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
        self.config = Config.get_conf(self, identifier=1357924680, force_registration=True)
        default_guild = {
            "auto_channel_id": None,
            "auto_message_id": None,
            "auto_enabled": False,
            "notification_channel_id": None,
            "notify_events": []  # List of event names to notify about
        }
        self.config.register_guild(**default_guild)
        self.update_task: Optional[asyncio.Task] = None

    async def cog_load(self):
        """Start the auto-update task when cog loads."""
        self.update_task = asyncio.create_task(self._auto_update_loop())

    async def cog_unload(self):
        """Cancel the auto-update task when cog unloads."""
        if self.update_task:
            self.update_task.cancel()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def _get_current_hour(self) -> int:
        """Get the current UTC hour."""
        return datetime.now(timezone.utc).hour

    def _get_rotation(self, hour: int) -> dict:
        """Get the rotation data for a specific hour."""
        return self.MAP_ROTATIONS[hour % 24]

    def _get_current_rotation(self) -> dict:
        """Get the current rotation data."""
        return self._get_rotation(self._get_current_hour())

    def _get_next_rotation(self) -> Tuple[dict, int]:
        """Get the next rotation data and minutes until it starts."""
        now = datetime.now(timezone.utc)
        next_hour = (now.hour + 1) % 24
        minutes_until = 60 - now.minute
        return self._get_rotation(next_hour), minutes_until

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

        embed.set_footer(text=f"Hour {rotation['hour']}:00 UTC | Rotations change hourly")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    def _build_overview_embed(self) -> discord.Embed:
        """Build an overview embed with current and next rotation."""
        current = self._get_current_rotation()
        next_rot, minutes = self._get_next_rotation()

        embed = discord.Embed(
            title="\U0001F3AE Arc Raiders Map Rotation",
            description=f"**Current Hour:** {current['hour']}:00 UTC\n**Next rotation in:** {minutes} minutes",
            color=0x7B68EE
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

        embed.add_field(name=f"\U0001F7E2 Next Hour ({next_rot['hour']}:00 UTC)", value=next_text, inline=False)

        embed.set_footer(text="Data updates every hour | Based on UTC time")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def arc(self, ctx: commands.Context):
        """Arc Raiders map rotation commands."""
        embed = self._build_overview_embed()
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

        current_hour = self._get_current_hour()

        embed = discord.Embed(
            title=f"{map_info['emoji']} {map_info['name']} - 24 Hour Schedule",
            color=0x7B68EE
        )

        schedule_text = ""
        for rotation in self.MAP_ROTATIONS:
            hour = rotation["hour"]
            status = self._get_map_status(rotation, map_key)
            indicator = "\U0001F534" if hour == current_hour else "\u26AA"
            schedule_text += f"{indicator} **{hour:02d}:00** - {status}\n"

            # Split into multiple fields if too long
            if len(schedule_text) > 900:
                embed.add_field(name="\u200b", value=schedule_text, inline=False)
                schedule_text = ""

        if schedule_text:
            embed.add_field(name="\u200b", value=schedule_text, inline=False)

        embed.set_footer(text=f"Current hour: {current_hour}:00 UTC | \U0001F534 = Now")
        await ctx.send(embed=embed)

    @arc.command(name="event")
    async def arc_event(self, ctx: commands.Context, *, event_name: str):
        """Find when a specific event occurs across all maps."""
        # Find the event
        event_key = None
        for key in self.EVENTS.keys():
            if event_name.lower() == key.lower():
                event_key = key
                break

        if not event_key or event_key == "None":
            event_list = ", ".join([k for k in self.EVENTS.keys() if k != "None"])
            await ctx.send(f"Event not found. Available events: {event_list}")
            return

        event_info = self.EVENTS[event_key]
        current_hour = self._get_current_hour()

        embed = discord.Embed(
            title=f"{event_info['emoji']} {event_key} Schedule",
            description=event_info["desc"],
            color=0xFF6B6B if event_info["major"] else 0x6BCB77
        )

        found_any = False
        for map_key, map_info in self.MAPS.items():
            occurrences = []
            for rotation in self.MAP_ROTATIONS:
                map_data = rotation.get(map_key, {})
                hour = rotation["hour"]

                if map_data.get("major") == event_key:
                    indicator = "\U0001F534" if hour == current_hour else ""
                    occurrences.append(f"{hour:02d}:00 (2x){indicator}")
                elif map_data.get("minor") == event_key:
                    indicator = "\U0001F534" if hour == current_hour else ""
                    occurrences.append(f"{hour:02d}:00{indicator}")

            if occurrences:
                found_any = True
                embed.add_field(
                    name=f"{map_info['emoji']} {map_info['name']}",
                    value=", ".join(occurrences),
                    inline=False
                )

        if not found_any:
            embed.description += "\n\n*This event is not scheduled in the current rotation.*"

        embed.set_footer(text=f"Current hour: {current_hour}:00 UTC | \U0001F534 = Now")
        await ctx.send(embed=embed)

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
    async def arc_auto_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for automatic rotation updates."""
        await self.config.guild(ctx.guild).auto_channel_id.set(channel.id)
        await ctx.send(f"Auto-update channel set to {channel.mention}.")

    @arc_auto.command(name="enable")
    @commands.admin_or_permissions(manage_guild=True)
    async def arc_auto_enable(self, ctx: commands.Context):
        """Enable automatic rotation updates."""
        channel_id = await self.config.guild(ctx.guild).auto_channel_id()
        if not channel_id:
            await ctx.send("Please set a channel first with `arc auto channel #channel`.")
            return
        await self.config.guild(ctx.guild).auto_enabled.set(True)
        await ctx.send("Auto-updates enabled. The rotation embed will update every hour.")

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

    async def _auto_update_loop(self):
        """Background task that updates rotation embeds every hour."""
        await self.bot.wait_until_ready()

        while True:
            try:
                # Calculate time until next hour
                now = datetime.now(timezone.utc)
                next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                sleep_seconds = (next_hour - now).total_seconds()

                # Wait until the next hour
                await asyncio.sleep(sleep_seconds + 5)  # +5 seconds buffer

                # Update all guilds with auto-updates enabled
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
                                # Message was deleted, create new one
                                msg = await channel.send(embed=embed)
                                await self.config.guild(guild).auto_message_id.set(msg.id)
                        else:
                            msg = await channel.send(embed=embed)
                            await self.config.guild(guild).auto_message_id.set(msg.id)

                    except discord.Forbidden:
                        pass
                    except Exception:
                        pass

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)  # Wait a minute on error and retry
