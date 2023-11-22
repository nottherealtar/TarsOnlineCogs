import discord
from discord.ext import commands, tasks
import aiohttp

class CoffeeCommits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.get_cog("Config")
        self.session = aiohttp.ClientSession()
        self.commit_check_loop.start()

    def cog_unload(self):
        self.commit_check_loop.cancel()
        self.bot.loop.create_task(self.session.close())

    @tasks.loop(minutes=30)
    async def commit_check_loop(self):
        for guild_id, guild_data in await self.config.all_guilds().items():
            if not guild_data["api_key"]:
                continue

            for repo_name, repo_data in guild_data["watchlist"].items():
                if not repo_data["enabled"]:
                    continue

                try:
                    commits = await self.fetch_commits(guild_data["api_key"], repo_name)
                    if commits:
                        for commit in commits:
                            await self.post_commit_info(guild_id, repo_name, commit)

                except Exception as e:
                    print(f"Error checking commits for {repo_name} in guild {guild_id}: {e}")

    async def fetch_commits(self, api_key, repo_name):
        url = f"https://api.github.com/repos/{repo_name}/commits"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def post_commit_info(self, guild_id, repo_name, commit_data):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel_id = await self.config.guild(guild).notification_channel()
        channel = guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="New Commit",
            description=commit_data["commit"]["message"],
            color=discord.Color.green()
        )
        embed.set_author(name=commit_data["commit"]["author"]["name"],
                         icon_url=commit_data["author"]["avatar_url"])
        embed.add_field(name="Repository", value=f"[{repo_name}](https://github.com/{repo_name})")

        await channel.send(embed=embed)

    @commands.group(name="coffeecommits")
    async def coffee_commits(self, ctx):
        """GitHub commits tracking commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.coffee_commits)

    @coffee_commits.command(name="setapikey")
    async def set_api_key(self, ctx, api_key):
        """Set the GitHub API key."""
        await self.config.guild(ctx.guild).api_key.set(api_key)
        await ctx.send("API key set successfully.")

    @coffee_commits.command(name="addrepo")
    async def add_repo(self, ctx, repo_name):
        """Add a GitHub repo to the watchlist."""
        async with self.config.guild(ctx.guild).watchlist() as watchlist:
            if repo_name not in watchlist:
                watchlist[repo_name] = {"enabled": True}
                await ctx.send(f"Added {repo_name} to the watchlist.")
            else:
                await ctx.send(f"{repo_name} is already in the watchlist.")

    @coffee_commits.command(name="removerepo")
    async def remove_repo(self, ctx, repo_name):
        """Remove a GitHub repo from the watchlist."""
        async with self.config.guild(ctx.guild).watchlist() as watchlist:
            if repo_name in watchlist:
                del watchlist[repo_name]
                await ctx.send(f"Removed {repo_name} from the watchlist.")
            else:
                await ctx.send(f"{repo_name} is not in the watchlist.")

    @coffee_commits.command(name="togglewatch")
    async def toggle_watch(self, ctx):
        """Toggle the commit watchlist on/off."""
        notifications_enabled = await self.config.guild(ctx.guild).notifications_enabled()
        await self.config.guild(ctx.guild).notifications_enabled.set(not notifications_enabled)
        state = "enabled" if not notifications_enabled else "disabled"
        await ctx.send(f"Commit watchlist has been {state}.")

    @coffee_commits.command(name="setchannel")
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for commit notifications."""
        await self.config.guild(ctx.guild).notification_channel.set(channel.id)
        await ctx.send(f"Notification channel set to {channel.mention}.")

    @coffee_commits.command(name="fetchcommits")
    async def fetch_commits_command(self, ctx, repo_name):
        """Fetch and display the latest commits from a GitHub repo."""
        try:
            commits = await self.fetch_commits(await self.config.guild(ctx.guild).api_key(), repo_name)
            if commits:
                for commit in commits:
                    await self.post_commit_info(ctx.guild.id, repo_name, commit)
            else:
                await ctx.send(f"No commits found for {repo_name}.")
        except Exception as e:
            await ctx.send(f"Error fetching commits: {e}")