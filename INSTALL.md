# Install checklist — TarsOnlineCafe + curated third-party cogs

Replace `[p]` with your bot prefix. Run these on Discord after the bot is online.

---

## 0. Update this repo first

```text
[p]repo update TarsOnlineCafe
[p]cog update
```

If the repo isn’t added yet:

```text
[p]repo add TarsOnlineCafe https://github.com/nottherealtar/TarsOnlineCogs
```

---

## 1. TarsOnlineCafe (yours)

### Guide + MEE6-style community pack

```text
[p]cog install TarsOnlineCafe tarscafe serverassistant levelroles giveaways customcommands sticky
[p]load tarscafe serverassistant levelroles giveaways customcommands sticky
[p]tarscafe
[p]tarscafe features
[p]serverassistant level enable
```

### AFK = cooldownbuddy (café BRB) — do **not** install a third-party `afk` cog

```text
[p]cog install TarsOnlineCafe cooldownbuddy
[p]load cooldownbuddy
```

Use `/brb` / `[p]brb` — not a separate AFK package.

### Optional fun pack

```text
[p]cog install TarsOnlineCafe powerlevel cafeslots cafeblackjack beanduel roasttoast coffee chaoscoin
[p]load powerlevel cafeslots cafeblackjack beanduel roasttoast coffee chaoscoin
```

---

## 2. Third-party repos

> Confirm each cog still exists with `[p]cog list <reponame>` after adding the repo. Names can change.

### vrt-cogs

```text
[p]repo add vrt-cogs https://github.com/vertyco/vrt-cogs
[p]cog install vrt-cogs metrics autoreact easytranslate emojisteal imagelog
[p]load metrics autoreact easytranslate emojisteal imagelog
```

| Cog | Notes |
|-----|--------|
| `metrics` | Server stats over time |
| `autoreact` | Bot reacts with everyone else |
| `easytranslate` | Free Google Translate + context menus |
| `emojisteal` | Steal emojis/stickers |
| `imagelog` | Logs deleted images — **privacy-sensitive**; read its data statement |

### maxcogs

```text
[p]repo add maxcogs https://github.com/ltzmax/maxcogs
[p]cog install maxcogs earthquake serversupporters holiday
[p]load earthquake serversupporters holiday
```

### Kreusada-Cogs

```text
[p]repo add kreusada-cogs https://github.com/Kreusada/Kreusada-Cogs
[p]cog install kreusada-cogs didyoumean colour
[p]load didyoumean colour
```

### AAA3A-cogs

```text
[p]repo add AAA3A-cogs https://github.com/AAA3A-AAA3A/AAA3A-cogs
[p]cog install AAA3A-cogs fakeidentities honeypot perform
[p]load fakeidentities honeypot perform
```

**Skipped on purpose**

| Cog | Why |
|-----|-----|
| `afk` | Use **`cooldownbuddy`** instead |
| `lock` | Use **`serverassistant lock` / `unlock`** instead |

---

## 3. Honeypot setup — READ BEFORE YOU CREATE THE CHANNEL

`honeypot` (AAA3A) creates a bait channel meant to catch selfbots/scammers and can **mute, kick, or ban** instantly.

### Warning (paste this in your mod channel before setup)

```text
⚠️ HONEYPOT WARNING
You are about to create a bait channel at the top of the server.
Anyone who posts there (including confused real members) may be
muted / kicked / banned depending on your honeypot action settings.

Before enabling:
1. Tell staff the channel is bait — not a real chat.
2. Prefer MUTE or KICK over BAN until you’re confident.
3. Never put important announcements only in that channel.
4. Double-check which action is configured after setup.
5. If a real member trips it, reverse the action and explain.

If you are unsure, do not load honeypot yet.
```

### Safer first-time settings

1. Load the cog only when staff are online.
2. Run the cog’s setup/help: `[p]help Honeypot` (or `[p]honeypot` if that’s the group).
3. Set action to **mute** (or the mildest option) first — not ban.
4. Create the channel, then **immediately** post a staff-only note in your mod-log that the honeypot exists.
5. Watch the first few trips before escalating to kick/ban.

---

## 4. After installs

```text
[p]cog list
[p]tarscafe list
```

Sync slash commands if new hybrid cogs don’t appear (`[p]slash sync` — depends on your Red setup).

---

## Quick “what should I load?” matrix

| Need | Use |
|------|-----|
| AFK / away | `cooldownbuddy` |
| Lock channels | `serverassistant` |
| Levels + level roles | `serverassistant` + `levelroles` |
| Giveaways / CC / sticky | `giveaways` / `customcommands` / `sticky` |
| Scam bait channel | `honeypot` (with warning above) |
| Translate / emoji steal / image log | vrt-cogs |
| Earthquakes / holidays / supporters | maxcogs |
| Did-you-mean / colour info | kreusada-cogs |
| Fake IDs / perform actions | AAA3A-cogs |
