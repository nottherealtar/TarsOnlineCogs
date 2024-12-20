import os
from redbot.core import commands, Config
from discord import Embed, User, File
import random
from datetime import datetime
from .icon_generator import generate_icon, clear_icon_cache

class HowCracked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "highest": {"user": None, "percentage": 0, "time": None},
            "lowest": {"user": None, "percentage": 100, "time": None},
        }
        self.config.register_global(**default_global)

    def get_cracked_percentage(self):
        """
        Generate a random cracked percentage with a controlled distribution.
        """
        return random.uniform(0, 100)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 86400 seconds = 1 day
    async def howcracked(self, ctx, user: User = None):
        """
        Rate the cracked level of a user or yourself.
        """
        # Define cool power levels and emojis
        cool_power_levels = [
            "Ultra Mega Super Cracked",
            "Super Duper Cracked",
            "Mega Cracked",
            "Cracked",
            "Kinda Cracked",
            "Not So Cracked",
            "Un-Cracked",
            "Butt-Crack-ed",
            "On-Crack",
            "Barely Cracked",
            "Slightly Cracked",
            "Moderately Cracked",
            "Highly Cracked",
            "Extremely Cracked",
            "Insanely Cracked",
            "Godly Cracked",
            "Legendary Cracked",
            "Mythical Cracked",
            "Ultimate Cracked",
        ]

        emojis = ["💯", "😎", "🔥", "🤯", "👀"]

        cool_ability_levels = [
            "Ultra Mega Super Charismatic",
            "Super Duper Strong",
            "Mega Intelligent",
            "Mildly Psychic",
            "Slightly Telekinetic",
            "Not So Nimble",
            "Un-coordinated",
            "Butt-Smooth Talker",
            "Crack-Head",
            "Intellect",
            "Rizz",
            "Barely Nimble",
            "Slightly Strong",
            "Moderately Intelligent",
            "Highly Psychic",
            "Extremely Telekinetic",
            "Insanely Nimble",
            "Godly Strong",
            "Legendary Intelligent",
            "Mythical Psychic",
            "Ultimate Telekinetic",
        ]
        
        # Get the user to rate
        target_user = user or ctx.author

        # Generate a random cracked percentage
        cracked_percentage = self.get_cracked_percentage()
        
        # Update the record if necessary
        highest = await self.config.highest()
        lowest = await self.config.lowest()
        if cracked_percentage > highest["percentage"]:
            highest = {"user": str(target_user), "percentage": cracked_percentage, "time": datetime.utcnow().timestamp()}
            await self.config.highest.set(highest)
        if cracked_percentage < lowest["percentage"]:
            lowest = {"user": str(target_user), "percentage": cracked_percentage, "time": datetime.utcnow().timestamp()}
            await self.config.lowest.set(lowest)

        # Determine the cool power level based on the percentage
        power_level = None
        if cracked_percentage < 5:
            power_level = "On-Crack"
        elif cracked_percentage < 10:
            power_level = "Butt-Crack-ed"
        elif cracked_percentage < 15:
            power_level = "Un-Cracked"
        elif cracked_percentage < 20:
            power_level = "Not So Cracked"
        elif cracked_percentage < 25:
            power_level = "Kinda Cracked"
        elif cracked_percentage < 30:
            power_level = "Barely Cracked"
        elif cracked_percentage < 35:
            power_level = "Slightly Cracked"
        elif cracked_percentage < 40:
            power_level = "Moderately Cracked"
        elif cracked_percentage < 50:
            power_level = "Cracked"
        elif cracked_percentage < 60:
            power_level = "Highly Cracked"
        elif cracked_percentage < 70:
            power_level = "Mega Cracked"
        elif cracked_percentage < 80:
            power_level = "Extremely Cracked"
        elif cracked_percentage < 90:
            power_level = "Super Duper Cracked"
        elif cracked_percentage < 95:
            power_level = "Insanely Cracked"
        elif cracked_percentage < 97:
            power_level = "Godly Cracked"
        elif cracked_percentage < 99:
            power_level = "Legendary Cracked"
        elif cracked_percentage < 100:
            power_level = "Mythical Cracked"
        else:
            power_level = "Ultra Mega Super Cracked"

        # Determine the cool ability level based on the percentage
        ability_level = None
        if cracked_percentage < 5:
            ability_level = "Crack-Head"
        elif cracked_percentage < 10:
            ability_level = "Un-coordinated"
        elif cracked_percentage < 15:
            ability_level = "Not So Nimble"
        elif cracked_percentage < 20:
            ability_level = "Mildly Psychic"
        elif cracked_percentage < 25:
            ability_level = "Slightly Telekinetic"
        elif cracked_percentage < 30:
            ability_level = "Barely Nimble"
        elif cracked_percentage < 35:
            ability_level = "Slightly Strong"
        elif cracked_percentage < 40:
            ability_level = "Moderately Intelligent"
        elif cracked_percentage < 50:
            ability_level = "Highly Psychic"
        elif cracked_percentage < 60:
            ability_level = "Extremely Telekinetic"
        elif cracked_percentage < 70:
            ability_level = "Insanely Nimble"
        elif cracked_percentage < 80:
            ability_level = "Godly Strong"
        elif cracked_percentage < 90:
            ability_level = "Legendary Intelligent"
        elif cracked_percentage < 95:
            ability_level = "Mythical Psychic"
        elif cracked_percentage < 97:
            ability_level = "Ultimate Telekinetic"
        else:
            ability_level = "Ultra Mega Super Charismatic"

        # Generate or retrieve the icon
        icon_path = generate_icon(power_level)
        if not icon_path:
            await ctx.send("Failed to generate icon.")
            return

        # Build the embed
        embed = Embed(title=f"How Cracked is {target_user.name}?", color=0x00ff00)
        embed.description = f"{target_user.mention} is {power_level}! {cracked_percentage:.2f}% {ability_level} {random.choice(emojis)}"
        embed.set_image(url=f"attachment://{os.path.basename(icon_path)}")
        embed.set_footer(text="Powered by the Cracked-o-Meter and Goku")

        # Send the embed with the icon
        await ctx.send(embed=embed, file=File(icon_path))

    @commands.command()
    @commands.is_owner()
    async def generate_icons(self, ctx):
        """
        Generate RPG-style icons for all levels.
        """
        levels = [
            "On-Crack", "Butt-Crack-ed", "Un-Cracked", "Not So Cracked", "Kinda Cracked",
            "Barely Cracked", "Slightly Cracked", "Moderately Cracked", "Highly Cracked",
            "Extremely Cracked", "Insanely Cracked", "Godly Cracked", "Legendary Cracked",
            "Mythical Cracked", "Ultimate Cracked", "Ultra Mega Super Cracked"
        ]
        for level in levels:
            generate_icon(level)
        await ctx.send("Icons generated and cached successfully.")

    @commands.command()
    @commands.is_owner()
    async def regenerate_icons(self, ctx):
        """
        Regenerate RPG-style icons for all levels.
        """
        levels = [
            "On-Crack", "Butt-Crack-ed", "Un-Cracked", "Not So Cracked", "Kinda Cracked",
            "Barely Cracked", "Slightly Cracked", "Moderately Cracked", "Highly Cracked",
            "Extremely Cracked", "Insanely Cracked", "Godly Cracked", "Legendary Cracked",
            "Mythical Cracked", "Ultimate Cracked", "Ultra Mega Super Cracked"
        ]
        clear_icon_cache()
        for level in levels:
            generate_icon(level)
        await ctx.send("Icons regenerated and cached successfully.")

    def is_owner(ctx):
        return ctx.bot.is_owner(ctx.author) or (ctx.guild is not None and ctx.guild.owner_id == ctx.author.id)

    @commands.command()
    @commands.check(is_owner)
    async def clearrecords(self, ctx):
        """
        Clear the highest and lowest cracked records.
        Only the bot owner or the server owner can use this command.
        """
        await self.config.highest.set({"user": None, "percentage": 0, "time": None})
        await self.config.lowest.set({"user": None, "percentage": 100, "time": None})
        await ctx.send("Cracked records have been cleared.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have the necessary permissions to run this command.")    

    @commands.command()
    async def record(self, ctx, record_type: str):
        if record_type not in ["highest", "lowest"]:
            await ctx.send("Invalid record type. Please specify either 'highest' or 'lowest'.")
            return

        record = await self.config.get_attr(record_type)()
        if record["user"] is None:
            await ctx.send(f"No {record_type} record found.")
            return

        record_date = datetime.fromtimestamp(record['time'])
        days_since_record = (datetime.utcnow() - record_date).days

        embed = Embed(title=f"{record_type.capitalize()} Cracked Record 😎", color=0x00ff00)
        embed.description = f"**{record['user']}** holds the record for the **{record_type}** cracked percentage with *{record['percentage']:.2f}%* 🔥 for `{days_since_record}` days ⌛"
        await ctx.send(embed=embed)

# Required to make the cog load
def setup(bot):
    bot.add_cog(HowCracked(bot))