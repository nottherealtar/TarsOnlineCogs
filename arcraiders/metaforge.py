"""Live Arc Raiders event schedule from the MetaForge community API."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import aiohttp

METAFORGE_SCHEDULE_URL = "https://metaforge.app/api/arc-raiders/events-schedule"
METAFORGE_ATTRIBUTION = "Live event data from metaforge.app/arc-raiders"
CACHE_TTL_SECONDS = 300

API_MAP_NAMES = {
    "Dam": "dam",
    "Buried City": "buriedCity",
    "Spaceport": "spaceport",
    "Blue Gate": "blueGate",
    "Stella Montis": "stellaMontis",
    "Riven Tides": "rivenTides",
}

INTERNAL_TO_API_MAP = {value: key for key, value in API_MAP_NAMES.items()}

EVENT_ALIASES = {
    "Night Raid": "Night",
    "Electromagnetic Storm": "Storm",
    "Cold Snap": "Cold",
    "Locked Gate": "Gate",
    "Hidden Bunker": "Bunker",
    "Lush Blooms": "Blooms",
    "Prospecting Probes": "Probes",
    "Husk Graveyard": "Husks",
    "Bird City": "Birds",
    "Launch Tower Loot": "Tower",
    "Uncovered Caches": "Caches",
}

MAJOR_EVENT_API_NAMES = {
    "Night Raid",
    "Electromagnetic Storm",
    "Cold Snap",
    "Locked Gate",
    "Hidden Bunker",
    "Hurricane",
    "Harvester",
    "Matriarch",
}

ALIAS_TO_API_NAMES: Dict[str, List[str]] = {}
for api_name, alias in EVENT_ALIASES.items():
    ALIAS_TO_API_NAMES.setdefault(alias.lower(), []).append(api_name)
for api_name in MAJOR_EVENT_API_NAMES | set(EVENT_ALIASES):
    ALIAS_TO_API_NAMES.setdefault(api_name.lower(), []).append(api_name)


class MetaForgeSchedule:
    """Fetches and parses MetaForge events-schedule with in-memory caching."""

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._events: Optional[List[dict]] = None
        self._cache_at: float = 0.0
        self._last_error: Optional[str] = None

    @property
    def has_live_data(self) -> bool:
        return bool(self._events)

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"User-Agent": "TarsOnlineCogs-ArcRaiders/1.0 (Discord bot)"},
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def refresh(self, force: bool = False) -> Optional[List[dict]]:
        now = time.monotonic()
        if not force and self._events is not None and (now - self._cache_at) < CACHE_TTL_SECONDS:
            return self._events

        await self.start()
        try:
            async with self._session.get(METAFORGE_SCHEDULE_URL) as response:
                if response.status != 200:
                    self._last_error = f"HTTP {response.status}"
                    return self._events
                payload = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
            self._last_error = str(exc)
            return self._events

        events = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(events, list) or not events:
            self._last_error = "Empty schedule response"
            return self._events

        self._events = events
        self._cache_at = now
        self._last_error = None
        return self._events

    def normalize_event(self, api_name: str) -> str:
        return EVENT_ALIASES.get(api_name, api_name)

    def is_major(self, api_name: str) -> bool:
        return api_name in MAJOR_EVENT_API_NAMES

    def _timestamp_ms(self, when: Optional[datetime] = None) -> int:
        moment = when or datetime.now(timezone.utc)
        return int(moment.timestamp() * 1000)

    def state_at(self, when: Optional[datetime] = None) -> Dict[str, Dict[str, str]]:
        """Return map_key -> {minor, major} for all maps with active events."""
        if not self._events:
            return {}

        ts = self._timestamp_ms(when)
        grouped: Dict[str, List[dict]] = {}
        for event in self._events:
            map_key = API_MAP_NAMES.get(event.get("map", ""))
            if not map_key:
                continue
            grouped.setdefault(map_key, []).append(event)

        state: Dict[str, Dict[str, str]] = {}
        for map_key, map_events in grouped.items():
            active = [
                event
                for event in map_events
                if event.get("startTime", 0) <= ts < event.get("endTime", 0)
            ]
            major_events = [event for event in active if self.is_major(event["name"])]
            minor_events = [event for event in active if not self.is_major(event["name"])]

            major = self.normalize_event(major_events[0]["name"]) if major_events else "None"
            minor = self.normalize_event(minor_events[0]["name"]) if minor_events else "None"
            state[map_key] = {"minor": minor, "major": major}

        return state

    def build_rotation(
        self,
        when: Optional[datetime] = None,
        *,
        hour_label: Optional[int] = None,
        map_keys: Optional[List[str]] = None,
    ) -> dict:
        moment = when or datetime.now(timezone.utc)
        state = self.state_at(moment)
        rotation = {"hour": hour_label if hour_label is not None else moment.hour}

        keys = map_keys or list(API_MAP_NAMES.values())
        for map_key in keys:
            slot = state.get(map_key, {"minor": "None", "major": "None"})
            rotation[map_key] = {
                "minor": slot.get("minor", "None"),
                "major": slot.get("major", "None"),
            }
        return rotation

    def minutes_until_next_change(self, when: Optional[datetime] = None) -> int:
        if not self._events:
            moment = when or datetime.now(timezone.utc)
            return max(1, 60 - moment.minute)

        ts = self._timestamp_ms(when)
        boundaries = set()
        for event in self._events:
            start = event.get("startTime", 0)
            end = event.get("endTime", 0)
            if start > ts:
                boundaries.add(start)
            if end > ts:
                boundaries.add(end)

        if not boundaries:
            return 60

        next_ts = min(boundaries)
        return max(1, (next_ts - ts) // 60000)

    def next_change_at(self, when: Optional[datetime] = None) -> datetime:
        minutes = self.minutes_until_next_change(when)
        moment = when or datetime.now(timezone.utc)
        return moment + timedelta(minutes=minutes)

    def map_timeline(
        self,
        map_key: str,
        *,
        hours: int = 24,
        when: Optional[datetime] = None,
    ) -> List[dict]:
        """Upcoming hourly slots for one map."""
        if not self._events:
            return []

        moment = when or datetime.now(timezone.utc)
        start_ts = self._timestamp_ms(moment)
        now_ts = self._timestamp_ms(moment)
        end_ts = start_ts + (hours * 3600 * 1000)

        slots = []
        for event in self._events:
            if API_MAP_NAMES.get(event.get("map", "")) != map_key:
                continue
            if event.get("endTime", 0) <= start_ts or event.get("startTime", 0) >= end_ts:
                continue

            start = datetime.fromtimestamp(event["startTime"] / 1000, tz=timezone.utc)
            is_major = self.is_major(event["name"])
            slots.append(
                {
                    "start": start,
                    "name": self.normalize_event(event["name"]),
                    "major": is_major,
                    "api_name": event["name"],
                    "active_now": event["startTime"] <= now_ts < event["endTime"],
                }
            )

        slots.sort(key=lambda slot: slot["start"])
        return slots

    def find_event_occurrences(self, query: str) -> List[dict]:
        """Find schedule entries matching an event name."""
        if not self._events:
            return []

        query_lower = query.lower().strip()
        api_names = ALIAS_TO_API_NAMES.get(query_lower, [])
        if not api_names and query_lower:
            api_names = [
                event["name"]
                for event in self._events
                if query_lower in event["name"].lower()
            ]

        api_name_set = set(api_names)
        now_ts = self._timestamp_ms()
        results = []
        for event in self._events:
            if event["name"] not in api_name_set:
                continue
            map_key = API_MAP_NAMES.get(event.get("map", ""))
            if not map_key:
                continue
            start = datetime.fromtimestamp(event["startTime"] / 1000, tz=timezone.utc)
            results.append(
                {
                    "map_key": map_key,
                    "start": start,
                    "name": self.normalize_event(event["name"]),
                    "major": self.is_major(event["name"]),
                    "active_now": event["startTime"] <= now_ts < event["endTime"],
                }
            )

        results.sort(key=lambda row: row["start"])
        return results

    def snapshot(self, map_keys: List[str], when: Optional[datetime] = None) -> Dict[str, Tuple[str, str]]:
        rotation = self.build_rotation(when, map_keys=map_keys)
        return {
            map_key: (
                rotation.get(map_key, {}).get("minor", "None"),
                rotation.get(map_key, {}).get("major", "None"),
            )
            for map_key in map_keys
        }
