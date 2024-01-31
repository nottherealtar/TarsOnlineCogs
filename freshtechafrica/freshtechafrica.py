#
#  _   _  ___ _____ _____ _   _ _____ ____  _____    _    _   _____  _    ____  
# | \ | |/ _ \_   _|_   _| | | | ____|  _ \| ____|  / \  | | |_   _|/ \  |  _ \ 
# |  \| | | | || |   | | | |_| |  _| | |_) |  _|   / _ \ | |   | | / _ \ | |_) |
# | |\  | |_| || |   | | |  _  | |___|  _ <| |___ / ___ \| |___| |/ ___ \|  _ < 
# |_| \_|\___/ |_|   |_| |_| |_|_____|_| \_\_____/_/   \_\_____|_/_/   \_\_| \_\
# 

import discord
from redbot.core import commands, data_manager
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import requests
import json
import logging

log = logging.getLogger("red.FreshdeskCog")

class FreshTechAfricaCreate(discord.ui.Modal, title="Create Ticket"):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.TextInput(label="Subject", placeholder="Enter the subject of the ticket.", style=discord.TextInputStyle.short))
        self.add_item(discord.ui.TextInput(label="Description", placeholder="Enter the description of the ticket.", style=discord.TextInputStyle.paragraph))
        self.add_item(discord.ui.Select(options=[
            discord.SelectOption(label="Urgent", value="1"),
            discord.SelectOption(label="High", value="2"),
            discord.SelectOption(label="Medium", value="3"),
            discord.SelectOption(label="Low", value="4")
        ], placeholder="Select the priority of the ticket.", min_values=1, max_values=1))

    async def on_submit(self, interaction: discord.Interaction):
        subject = self.children[0].value
        description = self.children[1].value
        priority = int(self.children[2].values[0])

        # Create a new ticket in Freshdesk
        ticket_data = {
            "description": description,
            "subject": subject,
            "priority": priority,
            "status": 2,
            "email": interaction.user.email,
            "name": interaction.user.display_name
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.bot.freshdesk_api_key
        }

        response = requests.post(
            f"https://{self.bot.freshdesk_domain}{self.bot.freshdesk_prefix}/tickets.json",
            headers=headers,
            data=json.dumps(ticket_data)
        )

        if response.status_code == 201:
            await interaction.response.send_message("Ticket created successfully!")
        else:
            await interaction.response.send_message("Failed to create ticket. Error: " + response.text)

class FreshTechAfricaUpdate(discord.ui.Modal, title="Update Ticket"):
    def __init__(self, ticket_id: int):
        super().__init__()
        self.ticket_id = ticket_id
        self.add_item(discord.ui.Select(options=[
            discord.SelectOption(label="Urgent", value="1"),
            discord.SelectOption(label="High", value="2"),
            discord.SelectOption(label="Medium", value="3"),
            discord.SelectOption(label="Low", value="4")
        ], placeholder="Select the new priority of the ticket.", min_values=1, max_values=1))
        self.add_item(discord.ui.Select(options=[
            discord.SelectOption(label="Open", value="2"),
            discord.SelectOption(label="Pending", value="3"),
            discord.SelectOption(label="Resolved", value="4"),
            discord.SelectOption(label="Closed", value="5")
        ], placeholder="Select the new status of the ticket.", min_values=1, max_values=1))
        self.add_item(discord.ui.TextInput(label="Agent", placeholder="Enter the name of the new agent for the ticket.", style=discord.TextInputStyle.short))

    async def on_submit(self, interaction: discord.Interaction):
        priority = int(self.children[0].values[0])
        status = int(self.children[1].values[0])
        agent = self.children[2].value

        # Update the ticket in Freshdesk
        ticket_data = {
            "ticket": {
                "status": {
                    "id": status
                },
                "priority": {
                    "id": priority
                },
                "agent": {
                    "name": agent
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.bot.freshdesk_api_key
        }

        response = requests.put(
            f"https://{self.bot.freshdesk_domain}{self.bot.freshdesk_prefix}/tickets/{self.ticket_id}.json",
            headers=headers,
            data=json.dumps(ticket_data)
        )

        if response.status_code == 200:
            await interaction.response.send_message("Ticket updated successfully!")
        else:
            await interaction.response.send_message("Failed to update ticket. Error: " + response.text)

class FreshTechAfrica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.freshdesk_domain = "your-freshdesk-domain.freshdesk.com"
        self.freshdesk_prefix = "/api/v2"
        self.config = data_manager.get_config("FreshdeskCog")

    async def get_api_key(self):
        return await self.config.api_key()

    async def set_api_key(self, key):
        await self.config.api_key.set(key)

    @commands.group(name="freshdesk")
    async def freshdesk_group(self, ctx):
        """Manage Freshdesk settings."""

    @freshdesk_group.command(name="setapikey")
    async def set_api_key_command(self, ctx, api_key: str):
        """Set the Freshdesk API key."""
        await self.set_api_key(api_key)
        await ctx.send("Freshdesk API key set successfully.")

    @freshdesk_group.command(name="create", help="Create a new ticket in Freshdesk")
    async def create_ticket(self, ctx):
        modal = FreshTechAfricaCreate()
        await modal.start(ctx)

    @freshdesk_group.command(name="update", help="Update a ticket in Freshdesk")
    async def update_ticket(self, ctx, ticket_id: int):
        modal = FreshTechAfricaUpdate(ticket_id)
        await modal.start(ctx)

    async def cog_check(self, ctx):
        if not await self.get_api_key():
            await ctx.send("Freshdesk API key is not set. Please set it using `{prefix}freshdesk setapikey <api_key>`.")
            return False
        return True

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return
