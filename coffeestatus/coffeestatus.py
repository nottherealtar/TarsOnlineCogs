#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

import discord
from redbot.core import Config, commands, checks
import asyncio
import logging

log = logging.getLogger("red.nottherealtar.coffeestatus")


class CoffeeStatus(commands.Cog):
    """Displays bot stats or sets a specific activity status."""

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2752521001, force_registration=True)

        self.presence_task = asyncio.create_task(self.maybe_update_presence())

        default_global = {
            "botstats": True,
            "activities": ["cchelp", "cccoffee", "ccthankyou"],
            "streamer": "nottherealtar",
            "type": 0,
            "status": 0,
        }
        self.config.register_global(**default_global)

    def cog_unload(self):
        self.presence_task.cancel()

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.is_owner()
    async def coffeestatus(self, ctx):
        """group commands."""
        pass

    @coffeestatus.command(name="activities")
    async def _activities(self, ctx, *activities: str):
        """Sets custom activities for the bot."""
        if activities == ():
            saved_activities = await self.config.activities()
            msg = (
                f"Current custom activities: {(', ').join(saved_activities)}\n"
                f"To set new activities, use the instructions in `{ctx.prefix}help coffeestatus activities`."
            )
            return await ctx.send(msg)
        await self.config.activities.set(list(activities))
        await self.presence_updater()
        await ctx.send("Done. Redo this command with no parameters to see the current list of activities.")

    @coffeestatus.command(name="streamer")
    async def _streamer(self, ctx: commands.Context, *, streamer=None):
        """Set the streamer name needed for streaming statuses."""
        saved_streamer = await self.config.streamer()
        if streamer is None:
            return await ctx.send(f"Current Streamer: {saved_streamer}")
        await self.config.streamer.set(streamer)
        await ctx.send("Done. Redo this command with no parameters to see the current streamer.")

    @coffeestatus.command()
    async def botstats(self, ctx):
        """Toggle for a bot stats status instead of random messages."""
        botstats = await self.config.botstats()
        await self.config.botstats.set(not botstats)
        await ctx.send(f"Botstats toggle: {not botstats}.")
        await self.presence_updater()

    @coffeestatus.command(name="type")
    async def _coffeestatus_type(self, ctx, status_type: int):
        """Define the coffeestatus game type.

        Type list:
        0 = Playing
        1 = Streaming
        2 = Listening
        3 = Watching
        5 = Competing"""
        if 0 <= status_type <= 3 or 0 != 5:
            rnd_type = {0: "playing", 1: "streaming", 2: "listening", 3: "watching", 5: "competing"}
            await self.config.type.set(status_type)
            await self.presence_updater()
            await ctx.send(f"Rndstatus activity type set to {rnd_type[status_type]}.")
        else:
            await ctx.send(
                f"Status activity type must be between 0 and 3 or 5. "
                f"See `{ctx.prefix}help rndstatus type` for more information."
            )

    @coffeestatus.command()
    async def status(self, ctx, status: int):
        """Define the rndstatus presence status.

        Status list:
        0 = Online
        1 = Idle
        2 = DND
        3 = Invisible"""
        if 0 <= status <= 3:
            rnd_status = {0: "online", 1: "idle", 2: "DND", 3: "invisible"}
            await self.config.status.set(status)
            await self.presence_updater()
            await ctx.send(f"Rndstatus presence status set to {rnd_status[status]}.")
        else:
            await ctx.send(
                f"Status presence type must be between 0 and 3. "
                f"See `{ctx.prefix}help rndstatus status` for more information."
            )

    async def maybe_update_presence(self):
        await self.bot.wait_until_red_ready()
        while True:
            try:
                await self.presence_updater()
            except Exception:
                log.exception("Something went wrong in maybe_update_presence task:")

            await asyncio.sleep(300)  # Assuming a default delay of 300 seconds

    async def presence_updater(self):
        cog_settings = await self.config.all()
        guilds = self.bot.guilds
        try:
            guild = next(g for g in guilds if not g.unavailable)
        except StopIteration:
            return
        botstats = cog_settings["botstats"]
        streamer = cog_settings["streamer"]
        _type = cog_settings["type"]
        _status = cog_settings["status"]

        url = f"https://www.twitch.tv/{streamer}"

        if _status == 0:
            status = discord.Status.online
        elif _status == 1:
            status = discord.Status.idle
        elif _status == 2:
            status = discord.Status.dnd
        elif _status == 3:
            status = discord.Status.offline

        if botstats:
            me = self.bot.user
            total_users = len(self.bot.users)
            servers = str(len(self.bot.guilds))
            botstatus = f"☕cchelp | 🧑 {total_users} | 🌐 {servers}🌵"
            if _type == 1:
                await self.bot.change_presence(activity=discord.Streaming(name=botstatus, url=url))
            else:
                await self.bot.change_presence(activity=discord.Activity(name=botstatus, type=_type), status=status)
        else:
            activities = cog_settings["activities"]
            if len(activities) > 0:
                new_activity = self.random_activity(activities)
                if _type == 1:
                    await self.bot.change_presence(activity=discord.Streaming(name=new_activity, url=url))
                else:
                    await self.bot.change_presence(
                        activity=discord.Activity(name=new_activity, type=_type), status=status
                    )