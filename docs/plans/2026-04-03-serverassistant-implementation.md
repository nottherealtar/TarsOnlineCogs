# ServerAssistant Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add color role picker with grouped dropdowns, upgrade poll to button-based slash command with auto-close, add bot-owner-only server owners command, and migrate all commands to hybrid (slash + prefix).

**Architecture:** Extend the existing single-file `serverassistant.py` cog. Add persistent `discord.ui.View` subclasses for the color picker and poll. Convert `commands.group` to `commands.hybrid_group` for slash command support. Store color picker channel/message IDs in guild config.

**Tech Stack:** discord.py 2.x, redbot.core (Config, commands), discord.ui (View, Select, Button), app_commands

---

### Task 1: Convert to Hybrid Commands

**Files:**
- Modify: `serverassistant/serverassistant.py:1-5` (imports)
- Modify: `serverassistant/serverassistant.py:39` (base group decorator)
- Modify: `serverassistant/serverassistant.py:62` (antispam group)
- Modify: `serverassistant/serverassistant.py:240` (autorole group)
- Modify: `serverassistant/serverassistant.py:455` (log group)

**Step 1: Add app_commands import**

Add `from discord import app_commands` to the imports at line 2.

**Step 2: Convert base group**

Change line 39 from:
```python
@commands.group(invoke_without_command=True)
```
to:
```python
@commands.hybrid_group(invoke_without_command=True, fallback="help")
```

**Step 3: Convert subgroups**

Change `antispam`, `autorole`, and `log` subgroups from `@serverassistant.group(...)` to `@serverassistant.hybrid_group(...)` with `fallback="show"` for each.

**Step 4: Update help embed**

Update the help embed field values to show slash command syntax alongside prefix syntax (e.g., `/serverassistant createcolorroles`).

**Step 5: Verify no syntax errors**

Run: `python -c "import ast; ast.parse(open('serverassistant/serverassistant.py').read()); print('OK')"`
Expected: OK

**Step 6: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: convert serverassistant to hybrid commands for slash support"
```

---

### Task 2: Add Color Picker Config and Color Map

**Files:**
- Modify: `serverassistant/serverassistant.py:14-22` (default_guild config)
- Modify: `serverassistant/serverassistant.py` (add COLOR_ROLES class-level constant)

**Step 1: Add config keys for color picker**

Add to `default_guild` dict:
```python
"colorpicker_channel": None,
"colorpicker_message": None,
```

**Step 2: Add COLOR_ROLES constant**

Add above the class or as a class attribute — a dict grouping colors by category:
```python
COLOR_ROLES = {
    "Warm": {
        "Red": discord.Color.red(),
        "Orange": discord.Color.orange(),
        "Yellow": discord.Color.gold(),
        "Gold": discord.Color.gold(),
        "Pink": discord.Color.magenta(),
    },
    "Cool": {
        "Blue": discord.Color.blue(),
        "Cyan": discord.Color.from_rgb(0, 255, 255),
        "Teal": discord.Color.teal(),
        "Indigo": discord.Color.from_rgb(75, 0, 130),
        "Violet": discord.Color.from_rgb(238, 130, 238),
        "Purple": discord.Color.purple(),
    },
    "Neutral": {
        "White": discord.Color.from_rgb(255, 255, 255),
        "Black": discord.Color.from_rgb(0, 0, 0),
        "Gray": discord.Color.from_rgb(128, 128, 128),
        "Silver": discord.Color.from_rgb(192, 192, 192),
        "Brown": discord.Color.from_rgb(139, 69, 19),
    },
    "Nature": {
        "Green": discord.Color.green(),
        "Lime": discord.Color.from_rgb(191, 255, 0),
    },
}
```

**Step 3: Refactor createcolorroles to use COLOR_ROLES**

Update the `create_color_roles` command to flatten `COLOR_ROLES` instead of defining its own dict.

**Step 4: Verify no syntax errors**

Run: `python -c "import ast; ast.parse(open('serverassistant/serverassistant.py').read()); print('OK')"`

**Step 5: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: add color picker config and shared COLOR_ROLES constant"
```

---

### Task 3: Build Color Picker View (Persistent UI)

**Files:**
- Modify: `serverassistant/serverassistant.py` (add ColorPickerView class after VerifyView)

**Step 1: Create ColorRoleSelect class**

```python
class ColorRoleSelect(discord.ui.Select):
    """A single dropdown for a color group."""

    def __init__(self, cog, group_name, colors):
        options = [
            discord.SelectOption(label=name, value=name)
            for name in colors
        ]
        super().__init__(
            placeholder=f"{group_name} Colors",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"serverassistant_color_{group_name.lower()}",
        )
        self.cog = cog
        self.all_color_names = []
        for group in COLOR_ROLES.values():
            self.all_color_names.extend(group.keys())

    async def callback(self, interaction: discord.Interaction):
        color_name = self.values[0]
        guild = interaction.guild
        member = interaction.user

        # Find the role
        role = discord.utils.get(guild.roles, name=color_name)
        if not role:
            await interaction.response.send_message(
                f"The **{color_name}** role doesn't exist. An admin needs to run `/serverassistant createcolorroles` first.",
                ephemeral=True,
            )
            return

        # Remove existing color roles
        existing_color_roles = [
            r for r in member.roles if r.name in self.all_color_names
        ]
        if existing_color_roles:
            await member.remove_roles(*existing_color_roles, reason="Color role change")

        # Assign new color role
        await member.add_roles(role, reason="Color role selection")
        await interaction.response.send_message(
            f"You've been given the **{color_name}** color role!",
            ephemeral=True,
        )
```

**Step 2: Create ColorPickerView class**

```python
class ColorPickerView(discord.ui.View):
    """Persistent color picker with grouped dropdowns."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        for group_name, colors in COLOR_ROLES.items():
            self.add_item(ColorRoleSelect(cog, group_name, colors))
```

**Step 3: Register persistent view in cog_load**

Update `cog_load` to add the persistent view:
```python
async def cog_load(self):
    self.bot.add_view(ColorPickerView(self))
```

**Step 4: Verify no syntax errors**

**Step 5: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: add persistent color picker view with grouped dropdowns"
```

---

### Task 4: Add Color Picker Setup Command

**Files:**
- Modify: `serverassistant/serverassistant.py` (add colorpicker subgroup after createcolorroles)

**Step 1: Add colorpicker setup command**

```python
@serverassistant.hybrid_group(invoke_without_command=True, fallback="show")
@commands.has_permissions(manage_roles=True)
async def colorpicker(self, ctx):
    """Color picker settings."""
    ch_id = await self.config.guild(ctx.guild).colorpicker_channel()
    channel = ctx.guild.get_channel(ch_id) if ch_id else None
    await ctx.send(f"Color picker channel: {channel.mention if channel else 'Not set up'}")

@colorpicker.command(name="setup")
@commands.has_permissions(manage_roles=True)
async def colorpicker_setup(self, ctx, channel: discord.TextChannel = None):
    """Set up the color role picker. Optionally specify a channel, or one will be created."""
    if channel is None:
        # Create a new channel
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                send_messages=False, add_reactions=False
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                send_messages=True, manage_messages=True
            ),
        }
        channel = await ctx.guild.create_text_channel(
            "color-roles", overwrites=overwrites, reason="Color picker setup"
        )

    embed = discord.Embed(
        title="Choose Your Role Color",
        description=(
            "Pick a color from the dropdowns below to set your name color!\n\n"
            "You can only have **one** color role at a time — "
            "choosing a new one will replace your current color."
        ),
        color=discord.Color.from_rgb(255, 255, 255),
    )
    view = ColorPickerView(self)
    msg = await channel.send(embed=embed, view=view)

    await self.config.guild(ctx.guild).colorpicker_channel.set(channel.id)
    await self.config.guild(ctx.guild).colorpicker_message.set(msg.id)

    await ctx.send(f"Color picker set up in {channel.mention}!")
```

**Step 2: Verify no syntax errors**

**Step 3: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: add colorpicker setup command with channel creation"
```

---

### Task 5: Upgrade Poll Command with Buttons and Auto-Close

**Files:**
- Modify: `serverassistant/serverassistant.py` (replace poll command, add PollView/PollButton classes)

**Step 1: Create PollButton class**

```python
class PollButton(discord.ui.Button):
    def __init__(self, label, emoji, option_index):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=emoji,
            custom_id=f"poll_{option_index}",
        )
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        old_vote = view.votes.get(interaction.user.id)
        view.votes[interaction.user.id] = self.option_index

        # Update embed with new counts
        await view.update_embed(interaction.message)

        if old_vote == self.option_index:
            await interaction.response.send_message("You already voted for this!", ephemeral=True)
        elif old_vote is not None:
            await interaction.response.send_message(
                f"Changed your vote to: **{view.options[self.option_index]}**", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"You voted for: **{view.options[self.option_index]}**", ephemeral=True
            )
```

**Step 2: Create PollView class**

```python
class PollView(discord.ui.View):
    EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self, question, options):
        super().__init__(timeout=300)  # 5 minutes
        self.question = question
        self.options = options
        self.votes = {}  # {user_id: option_index}

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, emoji=self.EMOJIS[i], option_index=i))

    def build_embed(self, closed=False):
        counts = {}
        for idx in range(len(self.options)):
            counts[idx] = sum(1 for v in self.votes.values() if v == idx)
        total = sum(counts.values())

        desc_lines = []
        for i, opt in enumerate(self.options):
            count = counts[i]
            pct = f" ({count / total * 100:.0f}%)" if total > 0 else ""
            bar = ""
            if closed and total > 0:
                filled = round(count / total * 10)
                bar = f" {'█' * filled}{'░' * (10 - filled)}"
            desc_lines.append(f"{self.EMOJIS[i]} **{opt}** — {count} vote{'s' if count != 1 else ''}{pct}{bar}")

        if closed:
            # Find winner(s)
            max_votes = max(counts.values())
            winners = [self.options[i] for i, c in counts.items() if c == max_votes]
            if total == 0:
                desc_lines.append("\n**No votes were cast.**")
            elif len(winners) == 1:
                desc_lines.append(f"\n**Winner: {winners[0]}!**")
            else:
                desc_lines.append(f"\n**Tie: {', '.join(winners)}!**")

        embed = discord.Embed(
            title=f"{'[CLOSED] ' if closed else ''}📊 {self.question}",
            description="\n".join(desc_lines),
            color=discord.Color.red() if closed else discord.Color.blue(),
        )
        if not closed:
            embed.set_footer(text="Poll closes in 5 minutes")
        else:
            embed.set_footer(text=f"Final results — {total} total vote{'s' if total != 1 else ''}")
        return embed

    async def update_embed(self, message):
        await message.edit(embed=self.build_embed())

    async def on_timeout(self):
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        # Update with final results
        embed = self.build_embed(closed=True)
        if hasattr(self, "message") and self.message:
            await self.message.edit(embed=embed, view=self)
```

**Step 3: Replace old poll command**

Replace the old poll command (lines 281-295) with:
```python
@serverassistant.command()
@app_commands.describe(
    question="The poll question",
    option1="First option (required)",
    option2="Second option (required)",
    option3="Third option",
    option4="Fourth option",
    option5="Fifth option",
    option6="Sixth option",
    option7="Seventh option",
    option8="Eighth option",
    option9="Ninth option",
    option10="Tenth option",
)
async def poll(self, ctx, question: str, option1: str, option2: str,
               option3: str = None, option4: str = None, option5: str = None,
               option6: str = None, option7: str = None, option8: str = None,
               option9: str = None, option10: str = None):
    """Create a poll with up to 10 options. Closes after 5 minutes."""
    options = [o for o in [option1, option2, option3, option4, option5,
                           option6, option7, option8, option9, option10] if o]
    view = PollView(question, options)
    embed = view.build_embed()
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg
```

**Step 4: Verify no syntax errors**

**Step 5: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: upgrade poll to button-based voting with 5min auto-close"
```

---

### Task 6: Add Server Owners Command (Bot Owner Only)

**Files:**
- Modify: `serverassistant/serverassistant.py` (add owners command)

**Step 1: Add owners command**

```python
@serverassistant.command(name="owners")
@commands.is_owner()
async def server_owners(self, ctx):
    """List all server owners that have the bot. (Bot owner only)"""
    owner_map = {}  # {owner_id: {"user": user_obj, "guilds": [guild_names]}}
    for guild in self.bot.guilds:
        oid = guild.owner_id
        if oid not in owner_map:
            owner_map[oid] = {"user": guild.owner, "guilds": []}
        owner_map[oid]["guilds"].append(guild.name)

    # Sort by server count descending
    sorted_owners = sorted(owner_map.values(), key=lambda x: len(x["guilds"]), reverse=True)

    embeds = []
    per_page = 10
    for page_start in range(0, len(sorted_owners), per_page):
        page_owners = sorted_owners[page_start:page_start + per_page]
        embed = discord.Embed(
            title="Server Owners",
            color=discord.Color.gold(),
        )
        for entry in page_owners:
            user = entry["user"]
            guilds = entry["guilds"]
            name = str(user) if user else f"Unknown ({entry.get('user_id', '?')})"
            value = f"**Servers ({len(guilds)}):** {', '.join(guilds)}"
            embed.add_field(name=name, value=value, inline=False)

        page_num = page_start // per_page + 1
        total_pages = (len(sorted_owners) + per_page - 1) // per_page
        embed.set_footer(text=f"Page {page_num}/{total_pages} — {len(self.bot.guilds)} total servers")
        embeds.append(embed)

    for embed in embeds:
        await ctx.send(embed=embed, ephemeral=True)
```

**Step 2: Verify no syntax errors**

**Step 3: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "feat: add bot-owner-only server owners listing command"
```

---

### Task 7: Update Help Embed and Final Cleanup

**Files:**
- Modify: `serverassistant/serverassistant.py:42-59` (help embed)

**Step 1: Update help embed fields**

Update the help embed to include the new commands and slash syntax. Add fields for:
- `/serverassistant colorpicker setup [channel]` — Set up the color role picker
- `/serverassistant poll question option1 option2 ...` — Create a poll
- `/serverassistant owners` — List server owners (Bot owner only)

Remove old poll syntax reference.

**Step 2: Verify no syntax errors**

Run: `python -c "import ast; ast.parse(open('serverassistant/serverassistant.py').read()); print('OK')"`

**Step 3: Commit**

```bash
git add serverassistant/serverassistant.py
git commit -m "docs: update help embed with new commands and slash syntax"
```
