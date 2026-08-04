#
# TarsCafe — repo guide: discover cogs, feature map, install hints.
#

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import discord
from discord import Embed
from redbot.core import commands

# (cog package name, short blurb, category)
_CATALOG: List[Tuple[str, str, str]] = [
    ("tarscafe", "This guide — feature map & cog help", "Guide"),
    ("serverassistant", "Moderation, XP, roles, starboard, polls, verify", "Community"),
    ("levelroles", "MEE6-style roles at ServerAssistant levels", "Community"),
    ("giveaways", "Button giveaways with end + reroll", "Community"),
    ("customcommands", "Custom `[p]name` text replies / tags", "Community"),
    ("sticky", "Sticky messages that stay near channel bottom", "Community"),
    ("scanner", "Flag young accounts on join", "Community"),
    ("verifyall", "Mass-assign verified role", "Community"),
    ("suggestme", "Suggestions with voting + staff approve", "Community"),
    ("cafewelcome", "ASCII welcome GIFs", "Cafe"),
    ("coffee", "Coffee order GIF + daily streaks", "Cafe"),
    ("coffeeinfo", "Live member/bot/boost voice channels", "Cafe"),
    ("coffeestatus", "Bot presence / activity manager", "Cafe"),
    ("chaoscoin", "Flip, roll, café oracle", "Fun"),
    ("beanduel", "Espresso/Latte/Cold Brew duels", "Fun"),
    ("cafeblackjack", "Button blackjack (`/blackjack`)", "Fun"),
    ("cafeslots", "Café slot machine", "Fun"),
    ("powerlevel", "DBZ scouter readings", "Fun"),
    ("roasttoast", "Roast or toast buttons", "Fun"),
    ("complimentroulette", "Weirdly specific compliments", "Fun"),
    ("cooldownbuddy", "BRB timers + ping deflection", "Fun"),
    ("howcracked", "Cracked-o-meter ratings", "Fun"),
    ("howgay", "Rainbow percentage meter", "Fun"),
    ("assky", "Random ASCII emoticons", "Fun"),
    ("teachme", "ZenQuotes inspiration", "Fun"),
    ("thankyou", "Thank-you embeds", "Fun"),
    ("arcraiders", "Arc Raiders map rotations", "Games"),
    ("gamedatemate", "Presence → Game Date Mate webhook", "Games"),
    ("InfiniCount", "Counting channel + anti-cheat", "Games"),
    ("passgen", "Password generator (DM)", "Tools"),
    ("projectpost", "Project announcement wizard", "Tools"),
]

_FEATURE_MAP: List[Tuple[str, str]] = [
    ("Levels / XP", "`serverassistant level` — enable with `level enable`"),
    ("Level roles", "`levelrole add <level> @role` (needs serverassistant)"),
    ("Welcome images", "`cafewelcome` / `cwset`"),
    ("Reaction & select roles", "`serverassistant reactionrole` · `rolemenu`"),
    ("Moderation", "`serverassistant kick|ban|mute|warn|purge`"),
    ("Anti-spam", "`serverassistant antispam`"),
    ("Verification", "`serverassistant verifybutton` · `verifyall`"),
    ("Giveaways", "`giveaway start <minutes> [winners] <prize>`"),
    ("Custom commands", "`cc add <name> <text>` then `[p]<name>`"),
    ("Sticky messages", "`sticky set <text>`"),
    ("Suggestions", "`suggest` (suggestme cog)"),
    ("Starboard", "`serverassistant starboard`"),
    ("Fun / café games", "`tarscafe list Fun`"),
]


class Tarscafe(commands.Cog):
    """Discover TarsOnlineCafe cogs and MEE6-style feature map."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        return

    def _loaded_names(self) -> set:
        return {c.__class__.__name__.lower() for c in self.bot.cogs.values()} | {
            getattr(c, "qualified_name", "").lower() for c in self.bot.cogs.values()
        }

    def _is_loaded(self, package: str) -> bool:
        # Package folder names vs cog class names differ; check both.
        cog = self.bot.get_cog(package) or self.bot.get_cog(package.capitalize())
        if cog:
            return True
        aliases = {
            "customcommands": "Customcommands",
            "levelroles": "Levelroles",
            "giveaways": "Giveaways",
            "cafeblackjack": "CafeBlackjack",
            "cafeslots": "Cafeslots",
            "powerlevel": "Powerlevel",
            "beanduel": "Beanduel",
            "roasttoast": "Roasttoast",
            "serverassistant": "ServerAssistant",
            "InfiniCount": "InfiniCount",
            "tarscafe": "Tarscafe",
            "sticky": "Sticky",
            "passgen": "PassGen",
            "chaoscoin": "Chaoscoin",
            "complimentroulette": "Complimentroulette",
            "cooldownbuddy": "Cooldownbuddy",
            "howcracked": "HowCracked",
            "howgay": "HowGay",
            "cafewelcome": "CafeWelcome",
            "coffeeinfo": "CoffeeInfo",
            "coffeestatus": "CoffeeStatus",
            "gamedatemate": "GameDateMate",
            "arcraiders": "ArcRaiders",
            "suggestme": "SuggestMe",
            "verifyall": "VerifyAll",
            "projectpost": "ProjectPost",
            "scanner": "Scanner",
            "assky": "AsSky",
            "teachme": "TeachMe",
            "thankyou": "ThankYou",
            "coffee": "Coffee",
        }
        cls = aliases.get(package)
        return bool(cls and self.bot.get_cog(cls))

    @commands.hybrid_group(name="tarscafe", aliases=["tars", "cafeguide"], invoke_without_command=True)
    async def tarscafe(self, ctx: commands.Context):
        """TarsOnlineCafe guide — features, cog list, install help."""
        if ctx.invoked_subcommand is not None:
            return
        emb = Embed(
            title="☕ TarsOnlineCafe",
            description=(
                "Your café-flavored Red cog pack.\n\n"
                f"`{ctx.clean_prefix}tarscafe features` — MEE6-style feature → command map\n"
                f"`{ctx.clean_prefix}tarscafe list [category]` — all cogs (+ loaded mark)\n"
                f"`{ctx.clean_prefix}tarscafe info <cog>` — what a cog does + install line\n"
                f"`{ctx.clean_prefix}tarscafe install` — copy-paste install block\n"
                f"`{ctx.clean_prefix}help <command>` — Red’s built-in help for any command"
            ),
            color=0x6F4E37,
        )
        emb.set_footer(text="Repo: github.com/nottherealtar/TarsOnlineCogs")
        await ctx.send(embed=emb)

    @tarscafe.command(name="features")
    async def tarscafe_features(self, ctx: commands.Context):
        """Map common MEE6-style features to commands in this repo."""
        lines = [f"**{title}** — {cmd}" for title, cmd in _FEATURE_MAP]
        emb = Embed(
            title="Feature map",
            description="\n".join(lines),
            color=0x6F4E37,
        )
        emb.set_footer(text="Load the matching cog first if a command is unknown.")
        await ctx.send(embed=emb)

    @tarscafe.command(name="list")
    async def tarscafe_list(self, ctx: commands.Context, category: Optional[str] = None):
        """List repo cogs. Optional category: Community, Cafe, Fun, Games, Tools, Guide."""
        cat_filter = category.title() if category else None
        by_cat: Dict[str, List[str]] = {}
        for pkg, blurb, cat in _CATALOG:
            if cat_filter and cat != cat_filter:
                continue
            mark = "✅" if self._is_loaded(pkg) else "⬜"
            by_cat.setdefault(cat, []).append(f"{mark} `{pkg}` — {blurb}")

        if not by_cat:
            await ctx.send("Unknown category. Try Community, Cafe, Fun, Games, Tools, Guide.")
            return

        emb = Embed(title="TarsOnlineCafe cogs", color=0x6F4E37)
        for cat, lines in by_cat.items():
            chunk = "\n".join(lines)
            if len(chunk) > 1024:
                chunk = chunk[:1000] + "\n…"
            emb.add_field(name=cat, value=chunk, inline=False)
        emb.set_footer(text="✅ loaded on this bot · ⬜ not loaded")
        await ctx.send(embed=emb)

    @tarscafe.command(name="info")
    async def tarscafe_info(self, ctx: commands.Context, cog_name: str):
        """Show blurb + install/load lines for a cog package name."""
        key = cog_name.strip()
        match = next((row for row in _CATALOG if row[0].lower() == key.lower()), None)
        if not match:
            await ctx.send("Unknown cog. Try `tarscafe list`.")
            return
        pkg, blurb, cat = match
        loaded = self._is_loaded(pkg)
        emb = Embed(title=f"`{pkg}`", description=blurb, color=0x6F4E37)
        emb.add_field(name="Category", value=cat, inline=True)
        emb.add_field(name="Loaded", value="yes" if loaded else "no", inline=True)
        emb.add_field(
            name="Install",
            value=(
                f"```\n"
                f"[p]cog install TarsOnlineCafe {pkg}\n"
                f"[p]load {pkg}\n"
                f"```"
            ),
            inline=False,
        )
        emb.add_field(
            name="Help",
            value=f"`{ctx.clean_prefix}help` after load, or try `{ctx.clean_prefix}{pkg}` / related groups.",
            inline=False,
        )
        await ctx.send(embed=emb)

    @tarscafe.command(name="install")
    async def tarscafe_install(self, ctx: commands.Context):
        """Copy-paste block to add the repo and recommended community pack."""
        text = (
            "```\n"
            "[p]repo add TarsOnlineCafe https://github.com/nottherealtar/TarsOnlineCogs\n"
            "[p]cog install TarsOnlineCafe tarscafe serverassistant levelroles "
            "giveaways customcommands sticky\n"
            "[p]load tarscafe serverassistant levelroles giveaways customcommands sticky\n"
            "```\n"
            f"Then `{ctx.clean_prefix}tarscafe features` for the command map.\n"
            "Fun pack: `powerlevel cafeslots cafeblackjack beanduel roasttoast coffee chaoscoin`"
        )
        await ctx.send(text)
