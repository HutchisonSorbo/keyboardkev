import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.Welcome")

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setwelcome", description="Update the welcome message (Admin only)")
    @app_commands.describe(message="New welcome message. Use {member} and {server} as placeholders.")
    async def setwelcome(self, interaction: discord.Interaction, message: str):
        # We assume DRAFT_ADMIN_ROLE is the generic admin role or we could use CUSTOM_CMD_ADMIN_ROLE
        # The prompt says: "/setwelcome [message] - Admin only. Updates the welcome message live without restarting."
        if not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        config.WELCOME_MESSAGE = message
        # Since config is loaded dynamically, this changes memory.
        await interaction.response.send_message(f"Welcome message updated for this session:\n\n{message}")
        log.info(f"Welcome message updated by {interaction.user}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Assign role
        if config.DEFAULT_ROLE:
            role = discord.utils.get(member.guild.roles, name=config.DEFAULT_ROLE)
            if role:
                try:
                    await member.add_roles(role)
                    log.info(f"Assigned {config.DEFAULT_ROLE} to {member.name}")
                except Exception as e:
                    log.error(f"Failed to assign role to {member.name}: {e}")
            else:
                log.warning(f"Default role {config.DEFAULT_ROLE} not found in {member.guild.name}")

        # Send welcome message
        channel = discord.utils.get(member.guild.text_channels, name=config.WELCOME_CHANNEL)
        msg_text = config.WELCOME_MESSAGE.format(member=member.mention, server=member.guild.name)
        
        if channel:
            embed = helpers.format_embed(
                title=f"Welcome to {config.SERVER_NAME}!",
                description=msg_text,
                colour=config.COLOUR_WELCOME
            )
            embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
            
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                log.error(f"Missing permissions to send welcome message in {member.guild.name} #{config.WELCOME_CHANNEL}")
        else:
            log.warning(f"Welcome channel {config.WELCOME_CHANNEL} not found in {member.guild.name}")

        # Send DM
        if config.WELCOME_DM:
            try:
                await member.send(config.WELCOME_DM)
            except discord.Forbidden:
                log.info(f"Could not send welcome DM to {member.name}, they probably have DMs disabled.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
