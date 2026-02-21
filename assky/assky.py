#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ <
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
#

import discord
from redbot.core import commands
import random


class AsSky(commands.Cog):
    """This cog produces random ASCII emojis when executed."""

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    async def assky(self, ctx):
        """
        Sends a random ASCII emoji from a large collection.

        Use this command for a fun, random ASCII face or emoticon!
        """
        emojis = [
            "( \u2022_\u2022)>\u2310\u25a0-\u25a0",
            "(\u2310\u25a0_\u25a0)",
            "\u00af\\_(\u30c4)_/\u00af",
            "(\u0361\u00b0 \u035c\u0296 \u0361\u00b0)",
            "\u1555(\u141b)\u1557",
            "\u0ca0_\u0ca0",
            "(\u256f\u00b0\u25a1\u00b0\uff09\u256f\ufe35 \u253b\u2501\u253b",
            "(\u3064\u00b0\u30ee\u00b0)\u3064",
            "\u0ca0\u2323\u0ca0",
            "(\u0e07'\u0300-'\u0301)\u0e07",
            "(\u028a\u8a00\u028a\u256c)",
            "\u028a\u203f\u028a",
            "(\u00b4\u2022  \u032e \u2022`)",
            "( \u0361~ \u035c\u0296 \u0361\u00b0)",
            "(\uff89\u25d5\u30ee\u25d5)\uff89*:\uff65\uff9f\u2727",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u00ac\u203f\u00ac)",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u0295\u2022\u1d25\u2022\u0294",
            "\u1633\u15e2\u1630",
            "(\u0e07\u00b0\u0644\u035c\u00b0)\u0e07",
            "\u0295\u2022\u0300\u03c9\u2022\u0301\u0294\u2727",
            "(\u00ac\u203f\u00ac)\uff89",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u0e07 \u2022\u0300_\u2022\u0301)\u0e07",
            "\u30fd(\u02c3\u30ee\u02c2)\uff89",
            "\u30fe(\u2310\u25a0_\u25a0)\uff89",
            "\u028a\u203f\u028a\u256c",
            "\u255a(\u2022\u2302\u2022)\u255d",
            "(\u028a\u203f\u028a)\u256f",
            "(\u3065\u25e1\ufe3f\u25e1)\u3065",
            "\u0295\u00b7\u1d25\u00b7\u0294",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u3063",
            "\u028a \u035c\u0296 \u028a",
            "\u252c\u2500\u252c\uff89(\u0ca0_\u0ca0\uff89)",
            "(\u0ca5\ufe3f\u0ca5)",
            "\uff08\u00b0o\u00b0\uff1b\uff09",
            "(\u0ca0_\u0ca0)",
            "\u0ca5_\u0ca5",
            "(\u00ac\u203f\u00ac)",
            "(\u00ac\u203f\u00ac)\uff89",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u256e(\u256f\u25bd\u2570)\u256d",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u30fd(\u2310\u25a0_\u25a0)\uff89",
            "\u30fe(\u2310\u25a0_\u25a0)\uff89",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u00ac\u203f\u00ac)\uff89",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u028a\u8a00\u028a\u256c)",
            "\u028a\u203f\u028a",
            "(\u028a\u203f\u028a)\u256f",
            "\u028a\u203f\u028a\u256c",
            "(\u00ac\u203f\u00ac)",
            "\u30fd(\u02c3\u30ee\u02c2)\uff89",
            "\u028a\u203f\u028a",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u3063",
            "\u30fe(\u2310\u25a0_\u25a0)\uff89",
            "(\u00ac\u203f\u00ac)\uff89",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u3063",
            "\u028a \u035c\u0296 \u028a",
            "\u252c\u2500\u252c\uff89(\u0ca0_\u0ca0\uff89)",
            "(\u2310\u25a0_\u25a0)",
            "(\u028a\u8a00\u028a\u256c)",
            "\u0295\u2022\u0300\u03c9\u2022\u0301\u0294\u2727",
            "\u30fd(\u2310\u25a0_\u25a0)\uff89",
            "(\u028a \u035c\u0296 \u028a)",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u3063",
            "(\u00ac\u203f\u00ac)",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u2727",
            "(\u2310\u25a0_\u25a0)",
            "\u0295\u2022\u0300\u03c9\u2022\u0301\u0294\u2727",
            "\u30fd(\u2310\u25a0_\u25a0)\uff89",
            "(\u00ac\u203f\u00ac)\uff89",
            "\u0295\u2022\u1d25\u2022\u0294",
            "\u1633\u15e2\u1630",
            "\u0295\u2022\u0300\u03c9\u2022\u0301\u0294\u2727",
            "\u1633\u15e2\u1630",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u028a\u203f\u028a",
            "(\u00b4\u2022  \u032e \u2022`)",
            "\u255a(\u2022\u2302\u2022)\u255d",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u0361\u00b0 \u035c\u0296 \u0361\u00b0)",
            "\u028a \u035c\u0296 \u028a",
            "(\u028a\u8a00\u028a\u256c)",
            "\uff08\u00b0o\u00b0\uff1b\uff09",
            "\u028a\u203f\u028a",
            "\uff08\u00b0o\u00b0\uff1b\uff09",
            "( \u0361~ \u035c\u0296 \u0361\u00b0)",
            "(\u2310\u25a0_\u25a0)",
            "(\u00b4\u2022  \u032e \u2022`)",
            "\u00af\\(\u00b0_o)/\u00af",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u028a \u035c\u0296 \u028a",
            "(\u028a \u035c\u0296 \u028a)",
            "\u028a\u203f\u028a",
            "\u255a(\u2022\u2302\u2022)\u255d",
            "\u1633\u15e2\u1630",
            "\u00af\\_(\u30c4)_/\u00af",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u2727",
            "\u0295\u2022\u1d25\u2022\u0294",
            "(\u3064\u00b0\u30ee\u00b0)\u3064",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u00ac\u203f\u00ac)",
            "\u00af\\(\u00b0_o)/\u00af",
            "(\u0e07 \u2022\u0300_\u2022\u0301)\u0e07",
            "\u30fd(\u02c3\u30ee\u02c2)\uff89",
            "\u30fe(\u2310\u25a0_\u25a0)\uff89",
            "\u028a\u203f\u028a\u256c",
            "\u255a(\u2022\u2302\u2022)\u255d",
            "(\u028a\u203f\u028a)\u256f",
            "(\u3065\u25e1\ufe3f\u25e1)\u3065",
            "\u0295\u00b7\u1d25\u00b7\u0294",
            "\u0295\u2022\u0301\u1d25\u2022\u0300\u0294\u3063",
            "\u028a \u035c\u0296 \u028a",
            "\u252c\u2500\u252c\uff89(\u0ca0_\u0ca0\uff89)",
            "(\u0ca5\ufe3f\u0ca5)",
            "(\u3064\u00b0\u30ee\u00b0)\u3064",
            "(\u0e07'\u0300-'\u0301)\u0e07",
            "\u0ca0\u2323\u0ca0",
            "( \u0361~ \u035c\u0296 \u0361\u00b0)",
            "(\uff89\u25d5\u30ee\u25d5)\uff89*:\uff65\uff9f\u2727",
        ]

        random_emoji = random.choice(emojis)
        await ctx.send(random_emoji)
