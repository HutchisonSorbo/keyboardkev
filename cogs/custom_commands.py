import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.CustomCommands")

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_cmds = {}

    async def cog_load(self):
        self.bot.loop.create_task(self.initialize_data())
        
    async def initialize_data(self):
        await self.bot.wait_until_ready()
        self.custom_cmds = await self.bot.db.load(config.CUSTOM_COMMANDS_FILE)
        await self.setup_default_commands()

    async def setup_default_commands(self):
        defaults = {
            "rules": "Check #rules for the full breakdown of how we operate before I ban ya.",
            "scoring": "Snake draft, 8 teams, 23 rounds. Standard AFL Fantasy scoring. Ask the Commish if confused, I'm too busy having a pint.",
            "prizes": "Prizes TBC. Mainly bragging rights and the eternal shame of last place. And you have to buy Kev a beer."
        }
        needs_save = False
        for cmd, resp in defaults.items():
            if cmd not in self.custom_cmds:
                self.custom_cmds[cmd] = resp
                needs_save = True
                
        if needs_save:
            await self.bot.db.save(config.CUSTOM_COMMANDS_FILE, self.custom_cmds)

    @app_commands.command(name="addcommand", description="Creates a new custom command")
    async def addcommand(self, interaction: discord.Interaction, trigger: str, response: str):
        if not helpers.has_role(interaction.user, config.CUSTOM_CMD_ADMIN_ROLE):
            await interaction.response.send_message("You don't have permission to add custom commands.", ephemeral=True)
            return
            
        trigger = trigger.lower()
        if trigger in self.custom_cmds:
            await interaction.response.send_message(f"Command `!{trigger}` already exists.", ephemeral=True)
            return
            
        # Basic sanitization
        response = response.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        if len(response) > config.CUSTOM_CMD_MAX_LENGTH:
            await interaction.response.send_message(f"Response too long (max {config.CUSTOM_CMD_MAX_LENGTH} chars).", ephemeral=True)
            return
            
        self.custom_cmds[trigger] = response
        await self.bot.db.save(config.CUSTOM_COMMANDS_FILE, self.custom_cmds)
        
        await interaction.response.send_message(f"✅ Added `!{trigger}`")

    @app_commands.command(name="deletecommand", description="Deletes a custom command")
    async def deletecommand(self, interaction: discord.Interaction, trigger: str):
        if not helpers.has_role(interaction.user, config.CUSTOM_CMD_ADMIN_ROLE):
            await interaction.response.send_message("You don't have permission to delete custom commands.", ephemeral=True)
            return
            
        trigger = trigger.lower()
        if trigger in self.custom_cmds:
            del self.custom_cmds[trigger]
            await self.bot.db.save(config.CUSTOM_COMMANDS_FILE, self.custom_cmds)
            await interaction.response.send_message(f"✅ Deleted `!{trigger}`")
        else:
            await interaction.response.send_message(f"Command `!{trigger}` not found.", ephemeral=True)

    @app_commands.command(name="editcommand", description="Edits an existing custom command")
    async def editcommand(self, interaction: discord.Interaction, trigger: str, response: str):
        if not helpers.has_role(interaction.user, config.CUSTOM_CMD_ADMIN_ROLE):
            await interaction.response.send_message("You don't have permission to edit custom commands.", ephemeral=True)
            return
            
        trigger = trigger.lower()
        if trigger not in self.custom_cmds:
            await interaction.response.send_message(f"Command `!{trigger}` not found.", ephemeral=True)
            return
            
        response = response.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        if len(response) > config.CUSTOM_CMD_MAX_LENGTH:
            await interaction.response.send_message(f"Response too long (max {config.CUSTOM_CMD_MAX_LENGTH} chars).", ephemeral=True)
            return
            
        self.custom_cmds[trigger] = response
        await self.bot.db.save(config.CUSTOM_COMMANDS_FILE, self.custom_cmds)
        
        await interaction.response.send_message(f"✅ Edited `!{trigger}`")

    @app_commands.command(name="listcommands", description="Lists all custom commands")
    async def listcommands(self, interaction: discord.Interaction):
        if not self.custom_cmds:
            await interaction.response.send_message("No custom commands configured.")
            return
            
        cmds_list = ", ".join([f"`!{c}`" for c in self.custom_cmds.keys()])
        embed = helpers.format_embed(
            title="Custom Commands",
            description=cmds_list,
            colour=config.COLOUR_HELP
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        if message.content.startswith("!"):
            trigger = message.content[1:].split()[0].lower()
            if trigger in self.custom_cmds:
                try:
                    await message.channel.send(self.custom_cmds[trigger])
                except discord.Forbidden:
                    log.error(f"Cannot send custom command reply in {message.channel.name}")

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
