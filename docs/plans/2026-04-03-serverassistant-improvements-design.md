# ServerAssistant Improvements Design

**Date:** 2026-04-03
**Scope:** Color role picker, poll upgrade, slash commands, server owners command

---

## 1. Color Role Picker

### Setup Command
- `/serverassistant colorpicker setup [channel]`
- If `channel` provided, sends the picker message there
- If omitted, creates a `#color-roles` channel and sends there
- Stores the channel ID and message ID in guild config for persistence

### Picker UI
- Embed with a friendly message ("Choose your role color below!")
- 4 grouped `discord.ui.Select` dropdowns:
  - **Warm** — Red, Orange, Yellow, Gold, Pink
  - **Cool** — Blue, Cyan, Teal, Indigo, Violet, Purple
  - **Neutral** — White, Black, Gray, Silver, Brown
  - **Nature** — Green, Lime
- Each dropdown: `max_values=1`, `min_values=1`
- Uses `custom_id` strings for persistence across restarts

### Behavior
- On selection: remove any existing color role from user, assign new one
- Ephemeral response confirming the change
- References the same 18 roles created by the existing `createcolorroles` command
- If the role doesn't exist yet, prompts user/admin to run `createcolorroles` first

---

## 2. Poll Command Upgrade

### Slash Command
- `/serverassistant poll question: option1: option2: [option3: ... option10:]`
- `question` — required string (supports spaces)
- `option1`, `option2` — required strings
- `option3` through `option10` — optional strings
- All string params naturally support multi-word input

### UI
- Embed with question as title, options listed with number emojis
- Button-based voting (one button per option with emoji + label)
- Buttons arranged in rows (max 5 per row, so up to 2 rows)

### Voting Logic
- Tracks votes in a dict: `{user_id: option_index}`
- Users can change their vote by clicking a different button
- Ephemeral confirmation on each vote ("You voted for: Pizza!")
- Embed updates live with current vote counts

### Auto-Close (5 minutes)
- After 5 minutes, poll automatically closes
- Buttons are disabled
- Embed updates with final results: vote counts, percentages, winner highlighted
- Uses `asyncio.sleep(300)` or `discord.utils.utcnow() + timedelta(minutes=5)` with view timeout

---

## 3. Slash Command Migration

- Convert `serverassistant` base group from `@commands.group()` to `@commands.hybrid_group()`
- Convert all subgroups to `@commands.hybrid_group()` as well
- All subcommands become accessible as both prefix and slash commands
- No behavioral changes to existing commands

---

## 4. Server Owners Command

### Command
- `/serverassistant owners`
- Restricted to bot owner via `@commands.is_owner()`

### UI
- Paginated embed(s) listing unique server owners
- For each owner:
  - Username and user ID
  - Number of servers they own (that have the bot)
  - Names of those servers
- Pagination if list exceeds embed limits
- Sorted by server count descending

### Security
- `@commands.is_owner()` — only the bot owner can run this
- No sensitive data leaks (server IDs not shown, just names)
- Ephemeral response option for extra privacy
