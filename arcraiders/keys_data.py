"""Arc Raiders keycard location data (community-sourced, jakebry/arc-raiders-map)."""

from __future__ import annotations

BLOB = "https://4avhgicb5hfji3xg.public.blob.vercel-storage.com"

MAP_INFO = {
    "dam": {"name": "Dam Battlegrounds", "preview": f"{BLOB}/images/preview/dam.jpg"},
    "spaceport": {"name": "Spaceport", "preview": f"{BLOB}/images/preview/spaceport.jpg"},
    "buried_city": {"name": "Buried City", "preview": f"{BLOB}/images/preview/buried_city.jpg"},
    "blue_gate": {"name": "Blue Gate", "preview": f"{BLOB}/images/preview/blue_gate_zoomed.jpg"},
    "stella_montis": {"name": "Stella Montis", "preview": f"{BLOB}/images/preview/stella_montis.jpg"},
    "riven_tides": {"name": "Riven Tides"},
}

RARITY_COLORS = {
    "uncommon": 0x4ADE80,
    "rare": 0x60A5FA,
    "epic": 0xCD3197,
}

RARITY_LABELS = {
    "uncommon": "Uncommon",
    "rare": "Rare",
    "epic": "Epic",
}

KEYS = [
    {
        "id": "dam_surveillance",
        "map": "dam",
        "name": "Dam Surveillance Key",
        "rarity": "uncommon",
        "location": "Water Treatment Control — Southwestern Hallway",
        "door_image": f"{BLOB}/images/doors/dam_battlegrounds/surveillance_door.webp",
        "description": "Unlocks a door in the Water Treatment Control building in The Dam.",
        "instructions": (
            "Surveillance Key opens a room in Water Treatment Control, a building in the "
            "southwest of the map, on the edge of the swamps. To enter the room, go northwest "
            "from the Water Treatment Elevator extraction, then go down to the door on the "
            "building's south side. Enter it and turn right, go through the alarm gate, and "
            "turn right again. It's the door opposite the camera."
        ),
    },
    {
        "id": "dam_staff_room",
        "map": "dam",
        "name": "Dam Staff Room Key",
        "rarity": "uncommon",
        "location": "Research & Administration — First Floor",
        "door_image": f"{BLOB}/images/doors/dam_battlegrounds/staff_room_door.webp",
        "description": "Unlocks a door in the Research and Administration building on Dam Battlegrounds.",
        "instructions": (
            "It's on the first floor of the building. You can get there virtually from any side "
            "of the building, except east and south. It's the door opposite the western entrance. "
            "The entrance is usually guarded by a Bombardier or a Bastion."
        ),
    },
    {
        "id": "dam_testing_annex",
        "map": "dam",
        "name": "Dam Testing Annex Key",
        "rarity": "rare",
        "location": "Testing Annex — Ground Floor (Two Doors)",
        "door_image": f"{BLOB}/images/doors/dam_battlegrounds/testing_annex_door.jpg",
        "description": "Unlocks a door in the Testing Annex on Dam Battlegrounds.",
        "instructions": (
            "Go to the southeast side of the map. The location has an extraction available close "
            "to it. One special thing about this key is that it can open one of the two doors on "
            "the ground floor of the building. Reach them through the parking lot entrance facing "
            "the Control Tower."
        ),
    },
    {
        "id": "dam_control_tower",
        "map": "dam",
        "name": "Dam Control Tower Key",
        "rarity": "epic",
        "location": "Control Tower — Top Floor",
        "door_image": f"{BLOB}/images/doors/dam_battlegrounds/control_tower_door.webp",
        "description": "Unlocks a door inside Control Tower on Dam Battlegrounds.",
        "instructions": (
            "One of the best Dam key rooms. Rush there fast — other key holders will too. Bring "
            "grenades and mines; the single exit is often camped. On the very top of the building "
            "— rappel up the elevator shaft. Watch for turrets guarding the shaft."
        ),
    },
    {
        "id": "sp_trench_tower",
        "map": "spaceport",
        "name": "Spaceport Trench Tower Key",
        "rarity": "uncommon",
        "location": "North or South Trench Tower (Between West/East Hangers)",
        "door_image": f"{BLOB}/images/doors/spaceport/trench_tower_door.webp",
        "description": "Unlocks a door to the Trench Towers in Spaceport.",
        "instructions": "Accesses a tower overlooking trench routes. Strong positional advantage but heavily contested.",
    },
    {
        "id": "sp_warehouse",
        "map": "spaceport",
        "name": "Spaceport Warehouse Key",
        "rarity": "uncommon",
        "location": "Shipping Warehouse — Top of Catwalk",
        "door_image": f"{BLOB}/images/doors/spaceport/warehouse_door.jpg",
        "description": "Unlocks a door in the Shipping Warehouse in Spaceport.",
        "instructions": "Grants access to large indoor loot zones. Warehouses are noisy to loot and frequently patrolled.",
    },
    {
        "id": "sp_ground_control",
        "map": "spaceport",
        "name": "Spaceport Control Tower Key",
        "rarity": "uncommon",
        "location": "Ground Control Tower — Upper Level",
        "door_image": f"{BLOB}/images/doors/spaceport/control_tower_door.webp",
        "description": "Unlocks a door to the Ground Control Tower in Spaceport.",
        "instructions": "High-ground interiors with valuable loot. High visibility makes prolonged looting dangerous.",
    },
    {
        "id": "sp_container_storage",
        "map": "spaceport",
        "name": "Spaceport Container Storage Key",
        "rarity": "rare",
        "location": "Container Storage — Top Floor Red Door",
        "door_image": f"{BLOB}/images/doors/spaceport/container_storage_doors.jpg",
        "description": "Unlocks a door in the Container Storage in Spaceport.",
        "instructions": "Used on shipping containers containing loot caches. Containers are exposed and easy to third-party.",
    },
    {
        "id": "bc_residential",
        "map": "buried_city",
        "name": "Buried City Residential Master Key",
        "rarity": "uncommon",
        "location": "Plaza Rosa Area / Grandioso Apartments",
        "door_image": f"{BLOB}/images/doors/buried_city/residential_grandioso.jpg",
        "description": "Unlocks certain apartment doors in Buried City.",
        "instructions": (
            "Two use areas: west of Plaza Rosa (building next to Main Street), and the northern "
            "building of Grandioso Apartments on the first floor. Grandioso Apartments is usually "
            "the better unlock."
        ),
    },
    {
        "id": "bc_jkv",
        "map": "buried_city",
        "name": "Buried City JKV Employee Card",
        "rarity": "uncommon",
        "location": "Space Travel Building — Northeast Section",
        "door_image": f"{BLOB}/images/doors/buried_city/jkv_access_door.webp",
        "description": "Unlocks a door in the J Kozma Ventures company building in Buried City.",
        "instructions": "Go to the Space Travel building and reach its 4th floor to find the locked room.",
    },
    {
        "id": "bc_hospital",
        "map": "buried_city",
        "name": "Buried City Hospital Key",
        "rarity": "rare",
        "location": "Hospital — Third Floor Northwest",
        "door_image": f"{BLOB}/images/doors/buried_city/hospital_door.webp",
        "description": "Unlocks a door in the Hospital in Buried City.",
        "instructions": (
            "Enter through the entrance facing the Library, turn left and walk straight until you "
            "face the room (often guarded by a turret). Turn left to see the locked door."
        ),
    },
    {
        "id": "bc_town_hall",
        "map": "buried_city",
        "name": "Buried City Town Hall Key",
        "rarity": "epic",
        "location": "Town Hall — Northern Side Ground Level",
        "door_image": f"{BLOB}/images/doors/buried_city/town_hall_entrance.webp",
        "description": "Unlocks a door to the Town Hall in Buried City.",
        "instructions": (
            "Unlocks not just a room but the whole building — one of the best keycards in the game. "
            "Often a PvP hotspot, but the open area is easy to defend once inside."
        ),
    },
    {
        "id": "bg_village",
        "map": "blue_gate",
        "name": "Blue Gate Village Key",
        "rarity": "uncommon",
        "location": "Village — House with Barred Front Door",
        "door_image": f"{BLOB}/images/doors/blue_gate/village_door.jpg",
        "description": "Unlocks a door to one of the old village buildings on Blue Gate.",
        "instructions": "Poor loot even during Night Raids, but very safe — few players bother with this door.",
    },
    {
        "id": "bg_patrol_car",
        "map": "blue_gate",
        "name": "Blue Gate Patrol Car Key",
        "rarity": "uncommon",
        "location": "Traffic Tunnel — Armored Patrol Car Rear Door",
        "description": "Unlocks the rear door of a patrol car on Blue Gate.",
        "instructions": (
            "Fits any armored patrol car inside the tunnel. Not much loot inside, but decent for "
            "weapon farming."
        ),
    },
    {
        "id": "bg_comm_tower",
        "map": "blue_gate",
        "name": "Blue Gate Communication Tower Key",
        "rarity": "rare",
        "location": "Communication Tower — Underground Storage Room",
        "door_image": f"{BLOB}/images/doors/blue_gate/comm_tower_door.webp",
        "description": "Unlocks the communication tower door at Blue Gate.",
        "instructions": (
            "Ground floor of Pilgrim's Peak, far end next to the elevator shaft. Lots of electrical "
            "loot; reliable but unsatisfying drops."
        ),
    },
    {
        "id": "bg_cellar",
        "map": "blue_gate",
        "name": "Blue Gate Cellar Key",
        "rarity": "rare",
        "location": "Cellar South of Ruined Homestead",
        "door_image": f"{BLOB}/images/doors/blue_gate/cellar_door_1.webp",
        "description": "Unlocks certain cellar doors near the Blue Gate.",
        "instructions": (
            "Locked cellar near the Olive Grove on the west side. High-value loot possible. Usually "
            "quiet but visible from players moving west from Ancient Fort."
        ),
    },
    {
        "id": "bg_confiscation",
        "map": "blue_gate",
        "name": "Blue Gate Confiscation Room Key",
        "rarity": "epic",
        "location": "Headhouse — Underground Tunnel System",
        "door_image": f"{BLOB}/images/doors/blue_gate/confiscation_door.jpg",
        "description": "Unlock a door to the confiscated foods area in the Blue Gate tunnels.",
        "instructions": (
            "Hug the left wall inside the big tunnel guarded by a Bastion or Bombardier until you "
            "see stairs. Go up, turn left — very hot PvP zone."
        ),
    },
    {
        "id": "sm_assembly",
        "map": "stella_montis",
        "name": "Stella Montis Assembly Admin Key",
        "rarity": "uncommon",
        "location": "Assembly — Central Corridor (Western Section)",
        "level": "upper",
        "door_image": f"{BLOB}/images/doors/stella_montis/assembly_admin_door.webp",
        "description": "Unlocks a door in Assembly in Stella Montis.",
        "instructions": "Restricted admin rooms. Good loot, but routes in and out are predictable.",
    },
    {
        "id": "sm_medical",
        "map": "stella_montis",
        "name": "Stella Montis Medical Storage Key",
        "rarity": "uncommon",
        "location": "Medical Research — North Side",
        "level": "upper",
        "door_image": f"{BLOB}/images/doors/stella_montis/medical_storage_door.webp",
        "description": "Unlocks a door in Medical Research in Stella Montis.",
        "instructions": "Healing-focused loot rooms. Often checked by players preparing for extended raids.",
    },
    {
        "id": "sm_archives",
        "map": "stella_montis",
        "name": "Stella Montis Archives Key",
        "rarity": "rare",
        "location": "Seed Vault — End of Tunnels",
        "level": "lower",
        "door_image": f"{BLOB}/images/doors/stella_montis/archives_storage_door.jpg",
        "description": "Unlocks a door in the Archives in Stella Montis.",
        "instructions": "Archive rooms with data-related loot. Tight interiors, easy to camp.",
    },
    {
        "id": "sm_security",
        "map": "stella_montis",
        "name": "Stella Montis Security Checkpoint Key",
        "rarity": "epic",
        "location": "Lobby — Northern Section",
        "level": "upper",
        "door_image": f"{BLOB}/images/doors/stella_montis/security_locked_room.jpg",
        "description": "Unlocks a door in the Security Checkpoint in Stella Montis.",
        "instructions": "Natural choke points — highly dangerous.",
    },
    {
        "id": "rt_hotel_102",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 102",
        "rarity": "uncommon",
        "location": "Hotel Panorama Azzurro — Floor 1, West Wing",
        "description": "Unlocks Room 102 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "End of the west-wing hallway on Floor 1, right next to Room 103. Pairs well with "
            "Room 103 for a quick west-wing double clear."
        ),
    },
    {
        "id": "rt_hotel_103",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 103",
        "rarity": "uncommon",
        "location": "Hotel Panorama Azzurro — Floor 1, West Wing",
        "description": "Unlocks Room 103 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "West-wing hallway on Floor 1, the door right next to Room 102. Quiet mid-tier loot "
            "run — good for budget loadouts."
        ),
    },
    {
        "id": "rt_hotel_107",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 107",
        "rarity": "epic",
        "location": "Hotel Panorama Azzurro — Floor 1, Central",
        "description": "Unlocks Room 107 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "Central section of Floor 1 — large double-bed suite with a balcony view. Best "
            "keycard on the map: high-tier weapons and an under-bed safe that is guaranteed to "
            "contain the Room 208 keycard on your first visit. Open 107 first, then chain into 208."
        ),
    },
    {
        "id": "rt_hotel_113",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 113",
        "rarity": "uncommon",
        "location": "Hotel Panorama Azzurro — Floor 1, East Wing",
        "description": "Unlocks Room 113 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": "End of the east-wing hallway on Floor 1.",
    },
    {
        "id": "rt_hotel_205",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 205",
        "rarity": "epic",
        "location": "Hotel Panorama Azzurro — Floor 2, Central",
        "description": "Unlocks Room 205 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "Central Floor 2 near the zipline. Turret-guarded interior — clear the turret before "
            "opening the door."
        ),
    },
    {
        "id": "rt_hotel_208",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 208",
        "rarity": "epic",
        "location": "Hotel Panorama Azzurro — Floor 2, Central-East",
        "description": "Unlocks Room 208 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "Central-east Floor 2 — multi-room suite, the largest locked area on Riven Tides. "
            "Often obtained from the safe under the bed in Room 107 on your first visit."
        ),
    },
    {
        "id": "rt_hotel_311",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 311",
        "rarity": "rare",
        "location": "Hotel Panorama Azzurro — Floor 3, East Tower",
        "description": "Unlocks Room 311 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "Base of the tall east-tower stairs on Floor 3. Chain with Room 404 up the east tower "
            "for a penthouse-tier run."
        ),
    },
    {
        "id": "rt_hotel_404",
        "map": "riven_tides",
        "name": "Riven Tides Hotel Keycard No. 404",
        "rarity": "epic",
        "location": "Hotel Panorama Azzurro — Floor 4, West Wing",
        "description": "Unlocks Room 404 in Hotel Panorama Azzurro on Riven Tides.",
        "instructions": (
            "End of the top-floor west hallway — penthouse-tier room. Reach via the east-tower "
            "stairwell from Floor 3 (Room 311 chain)."
        ),
    },
    {
        "id": "rt_crane_house",
        "map": "riven_tides",
        "name": "Riven Tides Crane House Keycard",
        "rarity": "uncommon",
        "location": "Stacking Yard — Top of Middle Crane",
        "description": "Unlocks the Crane House at the Stacking Yard on Riven Tides.",
        "instructions": (
            "South-central building at the Stacking Yard in the eastern part of the map. Reach the "
            "top of the middle crane via zipline or ladders."
        ),
    },
    {
        "id": "rt_classified_records",
        "map": "riven_tides",
        "name": "Riven Tides Classified Records Keycard",
        "rarity": "rare",
        "location": "Port Authority Building — Main Floor",
        "description": "Unlocks the Classified Records room in the Port Authority Building.",
        "instructions": (
            "Northwestern Port Authority Building. The room is at the bottom of the U-shaped corridor "
            "on the main floor — a Sentry often guards the locked doors upstairs."
        ),
    },
    {
        "id": "rt_secure_storage",
        "map": "riven_tides",
        "name": "Riven Tides Secure Storage Keycard",
        "rarity": "epic",
        "location": "Port Authority Building — Secure Storage",
        "description": "Unlocks the Secure Storage room in the Port Authority Building.",
        "instructions": (
            "Inside the Port Authority Building, near the Classified Records room. Often run as a "
            "dual-keycard route: clear the turret once, then open Classified Records and Secure "
            "Storage back to back."
        ),
    },
    {
        "id": "hatch_dam_1",
        "map": "dam",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Sunroof Hatch — Trees Above Ben Welder's Sunroof",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_dam_2",
        "map": "dam",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Spillway Hatch — South of Red Lakes Berm",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_sp_1",
        "map": "spaceport",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "West Elevator Hatch — West of Departure Building",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_sp_2",
        "map": "spaceport",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Central Elevator Hatch — East of Arrival Building",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_bc_1",
        "map": "buried_city",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Cargo Elevator Hatch",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_bc_2",
        "map": "buried_city",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Metro Station Hatch",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_bg_1",
        "map": "blue_gate",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Airshaft Extraction Point",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_bg_2",
        "map": "blue_gate",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Airshaft Extraction Point (East)",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_sm_1",
        "map": "stella_montis",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Assembly Workshops Hatch — Bottom Right of Assembly",
        "level": "upper",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
    {
        "id": "hatch_sm_2",
        "map": "stella_montis",
        "name": "Raider Hatch Key",
        "rarity": "rare",
        "location": "Sandbox B Hatch — Very South of Map",
        "level": "lower",
        "description": "Unlocks a raider hatch for quick extraction.",
        "instructions": "Emergency extraction hatch. Use for quick exits when under pressure.",
    },
]


def _normalize(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


MAP_QUERY_ALIASES = {
    "dam": ("dam", "dambattlegrounds", "battlegrounds", "the dam"),
    "spaceport": ("spaceport", "sp", "acerra"),
    "buried_city": ("buriedcity", "buried", "city", "bc"),
    "blue_gate": ("bluegate", "blue", "bg", "gate"),
    "stella_montis": ("stellamontis", "stella", "montis", "sm"),
    "riven_tides": ("riventides", "riven", "tides", "rt", "panorama", "hotel"),
}

# Rotation tracker map keys (arcraiders.MAPS) → keys_data map ids
ROTATION_TO_KEY_MAP = {
    "dam": "dam",
    "buriedCity": "buried_city",
    "spaceport": "spaceport",
    "blueGate": "blue_gate",
    "stellaMontis": "stella_montis",
    "rivenTides": "riven_tides",
}


def rotation_map_to_key_map(rotation_key: str) -> str | None:
    return ROTATION_TO_KEY_MAP.get(rotation_key)

KEY_ALIASES = {
    "staff room": "dam_staff_room",
    "surveillance": "dam_surveillance",
    "testing annex": "dam_testing_annex",
    "annex": "dam_testing_annex",
    "control tower": None,
    "town hall": "bc_town_hall",
    "hospital": "bc_hospital",
    "residential": "bc_residential",
    "jkv": "bc_jkv",
    "employee card": "bc_jkv",
    "patrol car": "bg_patrol_car",
    "confiscation": "bg_confiscation",
    "cellar": "bg_cellar",
    "village": "bg_village",
    "comm tower": "bg_comm_tower",
    "communication tower": "bg_comm_tower",
    "warehouse": "sp_warehouse",
    "container": "sp_container_storage",
    "trench": "sp_trench_tower",
    "assembly": "sm_assembly",
    "medical storage": "sm_medical",
    "archives": "sm_archives",
    "security checkpoint": "sm_security",
    "hotel 107": "rt_hotel_107",
    "hotel 208": "rt_hotel_208",
    "hotel 102": "rt_hotel_102",
    "hotel 103": "rt_hotel_103",
    "hotel 113": "rt_hotel_113",
    "hotel 205": "rt_hotel_205",
    "hotel 311": "rt_hotel_311",
    "hotel 404": "rt_hotel_404",
    "crane house": "rt_crane_house",
    "classified records": "rt_classified_records",
    "secure storage": "rt_secure_storage",
    "raider hatch": None,
    "hatch": None,
}


def _resolve_map_filter(query: str) -> tuple:
    """Pull a map filter out of the query when the user includes a map name."""
    words = query.lower().split()
    map_filter = None
    remaining = []

    for word in words:
        normalized = _normalize(word)
        matched = None
        for map_id, aliases in MAP_QUERY_ALIASES.items():
            if normalized in {_normalize(alias) for alias in aliases}:
                matched = map_id
                break
            if normalized in _normalize(MAP_INFO[map_id]["name"]):
                matched = map_id
                break
        if matched:
            map_filter = matched
        else:
            remaining.append(word)

    return map_filter, " ".join(remaining).strip() or query


def get_key_by_id(key_id: str) -> dict | None:
    for key in KEYS:
        if key["id"] == key_id:
            return key
    return None


def search_keys(query: str) -> list:
    """Case-insensitive key lookup with partial matching and optional map filtering."""
    raw = query.strip()
    if not raw:
        return []

    alias_target = None
    alias_query = raw.lower()
    for alias, key_id in KEY_ALIASES.items():
        if alias_query == alias or alias in alias_query:
            alias_target = key_id
            break

    if alias_target:
        key = get_key_by_id(alias_target)
        return [key] if key else []

    map_filter, search_text = _resolve_map_filter(raw)
    q = _normalize(search_text)
    if not q:
        return []

    words = [w for w in search_text.lower().split() if w]
    scored = []
    seen_ids = set()

    for key in KEYS:
        if map_filter and key["map"] != map_filter:
            continue

        name_norm = _normalize(key["name"])
        location_norm = _normalize(key.get("location", ""))
        map_norm = _normalize(MAP_INFO[key["map"]]["name"])
        id_norm = _normalize(key["id"])
        blob = f"{name_norm}{location_norm}{map_norm}{id_norm}"

        score = None
        if q == name_norm or q == id_norm:
            score = 0
        elif q in name_norm:
            score = 1
        elif all(_normalize(w) in blob for w in words):
            score = 2
        elif q in blob:
            score = 3

        if score is not None and key["id"] not in seen_ids:
            seen_ids.add(key["id"])
            scored.append((score, key))

    scored.sort(key=lambda item: (item[0], item[1]["name"], item[1]["location"]))
    return [key for _, key in scored]


def list_key_names() -> list:
    """Unique key names for help text."""
    seen = set()
    names = []
    for key in KEYS:
        if key["name"] not in seen:
            seen.add(key["name"])
            names.append(key["name"])
    return sorted(names, key=str.lower)


def list_key_choices() -> list:
    """All keys with disambiguated labels for slash autocomplete."""
    choices = []
    for key in KEYS:
        label = f"{key['name']} — {MAP_INFO[key['map']]['name']}"
        if key.get("location"):
            short_loc = key["location"]
            if len(short_loc) > 40:
                short_loc = short_loc[:37] + "..."
            label = f"{label} ({short_loc})"
        choices.append({"id": key["id"], "label": label})
    return choices
