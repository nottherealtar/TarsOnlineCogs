<div align="center">

# TarsOnlineCogs
v3 cogs for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) by **nottherealtar**

Café vibes · button games · MEE6-style community tools

[![Views](http://hits.dwyl.com/nottherealtar/TarsOnlineCogs.svg)](http://hits.dwyl.com/nottherealtar/TarsOnlineCogs)

**Dev server:** [Join here](https://discord.gg/CsR9zECCQt)

</div>

---

## Quick start

```text
[p]repo add TarsOnlineCafe https://github.com/nottherealtar/TarsOnlineCogs
[p]cog install TarsOnlineCafe tarscafe
[p]load tarscafe
[p]tarscafe
```

Then install what you need:

```text
[p]tarscafe install
[p]tarscafe features
[p]tarscafe list
[p]tarscafe info giveaways
```

**Full checklist** (this repo + curated third-party cogs, AFK = `cooldownbuddy`, honeypot warnings): see **[INSTALL.md](INSTALL.md)**.

| Goal | Commands |
|------|----------|
| Browse packages | `[p]cog list TarsOnlineCafe` |
| In-bot guide | `[p]tarscafe` / `[p]tarscafe features` |
| Red help | `[p]help <command>` or `[p]help <CogName>` |
| Update cogs | `[p]repo update TarsOnlineCafe` then `[p]cog update` |
| AFK / away | **`cooldownbuddy`** (`/brb`) — do not install a separate `afk` cog |

---

## Recommended community pack (MEE6-feeling)

Does **not** duplicate what `serverassistant` already does (XP, mod, reaction roles, starboard, verify).

```text
[p]cog install TarsOnlineCafe serverassistant levelroles giveaways customcommands sticky tarscafe
[p]load serverassistant levelroles giveaways customcommands sticky tarscafe
[p]serverassistant level enable
[p]levelrole add 5 @Regular
```

| Feature | Cog | Start here |
|---------|-----|------------|
| Levels / XP | `serverassistant` | `[p]serverassistant level` |
| Level roles | `levelroles` | `[p]levelrole` |
| Giveaways | `giveaways` | `[p]giveaway start` |
| Custom commands | `customcommands` | `[p]cc add` |
| Sticky messages | `sticky` | `[p]sticky set` |
| Mod / roles / starboard | `serverassistant` | `[p]serverassistant` |
| Feature map | `tarscafe` | `[p]tarscafe features` |

---

## All cogs

### Guide
| Cog | Description |
|-----|-------------|
| `tarscafe` | Feature map, cog catalog, install helpers |

### Community (MEE6-style)
| Cog | Description |
|-----|-------------|
| `serverassistant` | Moderation, anti-spam, autorole, verify, XP, starboard, reaction/select roles, polls |
| `levelroles` | Roles at ServerAssistant level thresholds |
| `giveaways` | Button enter / auto-end / reroll |
| `customcommands` | `[p]cc` tags → `[p]name` replies |
| `sticky` | Sticky channel messages |
| `scanner` | Flag young accounts on join |
| `verifyall` | Mass verified-role tool |
| `suggestme` | Suggestions + voting + staff approve |

### Café & utilities
| Cog | Description |
|-----|-------------|
| `cafewelcome` | ASCII welcome GIFs |
| `coffee` | Order GIF + daily streaks / boards |
| `coffeeinfo` | Live count voice channels |
| `coffeestatus` | Bot presence manager |
| `passgen` | Interactive password → DM |
| `projectpost` | Project announce wizard |
| `gamedatemate` | Presence → Game Date Mate webhook |

### Fun & games
| Cog | Description |
|-----|-------------|
| `arcraiders` | Arc Raiders map rotations |
| `beanduel` | Espresso / Latte / Cold Brew duels |
| `cafeblackjack` | `/blackjack` Hit/Stand/Double |
| `cafeslots` | `/slots` café reels |
| `chaoscoin` | Flip / roll / oracle |
| `complimentroulette` | Weird compliments |
| `cooldownbuddy` | `/brb` away timers |
| `powerlevel` | DBZ scouter |
| `roasttoast` | Roast / Toast buttons |
| `howcracked` / `howgay` | Percentage meters |
| `assky` / `teachme` / `thankyou` | Small fun utilities |
| `InfiniCount` | Counting channel |

---

## Requirements

Installed automatically by Downloader when needed:

| Cog | Pip deps |
|-----|----------|
| `gamedatemate` | aiohttp |
| `cafewelcome` | numpy, pillow |
| `howcracked` | pillow |
| `teachme` | aiohttp |

---

## Tips

- After installing new slash/hybrid cogs, sync if needed (`[p]slash sync` depending on your Red setup).
- `levelroles` **requires** `serverassistant` with leveling enabled — it does not run a second XP system.
- Prefer `[p]tarscafe features` over digging through source for “where is X?”.

---

## Other repos worth pairing

- [Red Cog Index](https://index.discord.red/)
- [Trusty-cogs](https://github.com/TrustyJAID/Trusty-cogs) · [AAA3A-cogs](https://github.com/AAA3A-AAA3A/AAA3A-cogs) · [FlameCogs](https://github.com/Flame442/FlameCogs)

Core Red already ships **Downloader**, **Scheduler**, **Economy**, **Modlog** — enable those before reinventing them.

---

<div align="center">

Open source — please credit where due. Made with coffee and code.

</div>
