<div align="center">
v3 Cogs for Red-DiscordBot by nottherealtar

[![Views](http://hits.dwyl.com/nottherealtar/TarsOnlineCogs.svg)](http://hits.dwyl.com/nottherealtar/TarsOnlineCogs)

> # TarsOnlineCogs
Welcome to my repo of weird and wacky duct-taped together cogs for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot).
This is a collection of cogs I have made over time—fun experiments, server utilities, and things I wanted for my own communities.

> Dev server: [Join here](https://discord.gg/CsR9zECCQt)

</div>

> # Current Available Cogs

### Server Management & Security
| Cog | Description | Status |
|-----|-------------|--------|
| `serverassistant` | Comprehensive server management with moderation tools, anti-spam, autorole, verification buttons, and logging | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `scanner` | Scans new members and flags young accounts for moderation review | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `verifyall` | Mass verification tool to assign verified role to members | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `suggestme` | Server suggestion system with voting and staff approval | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |

### Server Utilities
| Cog | Description | Status |
|-----|-------------|--------|
| `gamedatemate` | Game Date Mate: forward Discord presence to your web app (hybrid `/gamedatemate` setup) | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `cafewelcome` | Generates ASCII-themed welcome GIFs for new members | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `coffeeinfo` | Display server stats in auto-updating voice channels | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `coffeestatus` | Manage the bot's presence and activity status | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `InfiniCount` | Counting channel where users count +1 with anti-cheat | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `passgen` | Generates secure random passwords and sends via DM | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `projectpost` | Interactive project announcement embed creator | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |

### Fun & Games
| Cog | Description | Status |
|-----|-------------|--------|
| `arcraiders` | Arc Raiders map rotation tracker with auto-updates | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `chaoscoin` | **Chaos Coin:** `/chaos` flip, roll (2–100), ask — RNG with café oracle flavor (no economy) | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `complimentroulette` | **`/compliment`** — huge pool of weirdly specific praise; optional `@user` | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `cooldownbuddy` | **`/brb`** — easy minutes / `1h` / `at 3:30pm`; ping deflection + return proverbs | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `assky` | Sends a random ASCII emoji/emoticon | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `coffee` | Virtual coffee GIF (`order`), daily UTC **`checkin`** streaks, title ladder, **`board`** leaderboards | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `howcracked` | Rate the "cracked" level with RPG-style icons | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `howgay` | Fun rainbow percentage meter | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `teachme` | Get random inspirational quotes from ZenQuotes | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |
| `thankyou` | Send thank you messages to other users | ![Passing](https://img.shields.io/static/v1?label=Cog&message=Passing&color=brightgreen) |

***
<div align="center">

> ## Open source and available to the public—please credit where due.

> # Installation
1. Add the repo and install cogs via the Downloader cog:
    ```
    [p]repo add TarsOnlineCafe https://github.com/nottherealtar/TarsOnlineCogs
    [p]cog install TarsOnlineCafe <cog>
    [p]load <cog>
    ```

</div>

***

> ## Requirements
Some cogs have additional requirements that will be installed automatically:
- `gamedatemate` - aiohttp
- `cafewelcome` - numpy, pillow
- `howcracked` - pillow
- `teachme` - aiohttp

***

> ## Other open-source cogs worth adding

The wider Red ecosystem is huge. These are **third-party repos and cogs** (not part of this repo) that tend to stay maintained, show up on the official index, and **pair well** with what you already ship here—moderation, community tools, and light fun.

**Start here for discovery**

- **[Red Cog Index](https://index.discord.red/)** — searchable list of many approved cogs with copy-paste `repo add` / `cog install` lines. Always read each cog’s data/privacy notes and bot version requirements before installing.

**Curated repo picks**

| Repo | Why consider it | Example cogs |
|------|-----------------|----------------|
| [TrustyJAID/Trusty-cogs](https://github.com/TrustyJAID/Trusty-cogs) | Very active; utilities that complement custom mod stacks | **ReTrigger** (regex triggers), **ExtendedModLog** (richer server change logging), **RoleTools** (reaction / sticky roles) |
| [AAA3A-AAA3A/AAA3A-cogs](https://github.com/AAA3A-AAA3A/AAA3A-cogs) | Large, modern toolkit | Consolidated sanction-style flows, tickets/support-style workflows—useful if you want fewer one-off moderation bots |
| [Flame442/FlameCogs](https://github.com/Flame442/FlameCogs) | Good fit for gaming communities | **Gameroles** (roles when playing specific games—nice next to Arc Raiders / presence tooling), plus **Hangman**, **Battleship**, giveaways |
| [tmercswims/tmerc-cogs](https://github.com/tmercswims/tmerc-cogs) | Long-standing misc collection | Run `[p]cog list tmerc-cogs` after adding the repo; handy ports and small utilities |
| [laggron42/Laggrons-Dumb-Cogs](https://github.com/laggron42/Laggrons-Dumb-Cogs) | Classic Red v3 repo with extensive docs/wiki | Games and server tools—confirm each cog matches your Red version |
| [Cog-Creators/Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) (core) | Ships with Red | **Downloader**, **Scheduler** (reminders), **Economy**, core **Modlog**—enable bundled cogs before duplicating the same features from third parties |

**Caution:** Community cogs vary in maintenance and license (GPL vs MIT, etc.). Prefer repos with recent commits, open issues/PRs, and clear `info.json` metadata. Avoid overlapping loads (e.g. two heavy automod stacks) without testing on a staging bot first.

***

> ## Featured Cogs

### ServerAssistant
Full-featured server management cog with:
- **Anti-Spam Protection** - Configurable message limits, time windows, and actions (mute/kick/warn)
- **Moderation Tools** - Kick, ban, mute, unmute, warn, purge with role hierarchy checks
- **Autorole** - Automatically assign roles to new members
- **Verification Buttons** - Interactive verification system
- **Logging** - Track all moderation actions
- **Utilities** - Color roles, channel map, polls, server stats, user/role info

### Arc Raiders
Track Arc Raiders game map rotations:
- View current and upcoming map conditions
- Search by map or event type
- 24-hour UTC-based schedule
- Auto-updating embeds in designated channels
- All 5 maps: Dam, Buried City, Spaceport, Blue Gate, Stella Montis

***

<div align="center">

Made with coffee and code

</div>
