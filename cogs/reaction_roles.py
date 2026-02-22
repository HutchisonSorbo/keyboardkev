import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.ReactionRoles")

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rr_data = {}

    async def cog_load(self):
        self.rr_data = await self.bot.db.load("reaction_roles.json")

    @app_commands.command(name="reactionrole", description="Link an emoji to a role on a message (Admin only)")
    @app_commands.describe(channel="Channel with the message", message_id="ID of the message", emoji="Emoji to react with", role="Role to give")
    async def reactionrole(self, interaction: discord.Interaction, channel: discord.TextChannel, message_id: str, emoji: str, role: discord.Role):
        if not helpers.has_role(interaction.user, config.REACTION_ROLE_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role to configure reaction roles.", ephemeral=True)
            return
            
        try:
            msg = await channel.fetch_message(int(message_id))
        except Exception as e:
            await interaction.response.send_message(f"Could not find message. Make sure the ID and channel are correct. Error: {e}", ephemeral=True)
            return

        try:
            await msg.add_reaction(emoji)
        except Exception as e:
            await interaction.response.send_message(f"Could not add the reaction to the message. Is the emoji valid? {e}", ephemeral=True)
            return
            
        msg_id_str = str(msg.id)
        if msg_id_str not in self.rr_data:
            self.rr_data[msg_id_str] = {}
            
        self.rr_data[msg_id_str][emoji] = role.name
        await self.bot.db.save("reaction_roles.json", self.rr_data)
        
        await interaction.response.send_message(f"✅ Users who react with {emoji} to message `{message_id}` will receive the **{role.name}** role.")

    @app_commands.command(name="listreactionroles", description="List all configured reaction roles")
    async def listreactionroles(self, interaction: discord.Interaction):
        if not self.rr_data:
            await interaction.response.send_message("No reaction roles configured.")
            return
            
        desc = ""
        for msg_id, reactions in self.rr_data.items():
            desc += f"**Message [{msg_id}](https://discord.com/channels/{interaction.guild_id}/0/{msg_id})**\n"
            for emoji, role_name in reactions.items():
                desc += f"{emoji} ➔ @{role_name}\n"
            desc += "\n"
            
        embed = helpers.format_embed("Reaction Roles", desc, config.COLOUR_HELP)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removereactionrole", description="Remove a reaction role link (Admin only)")
    @app_commands.describe(message_id="ID of the message", emoji="The emoji to remove")
    async def removereactionrole(self, interaction: discord.Interaction, message_id: str, emoji: str):
        if not helpers.has_role(interaction.user, config.REACTION_ROLE_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role.", ephemeral=True)
            return
            
        if message_id in self.rr_data and emoji in self.rr_data[message_id]:
            role_name = self.rr_data[message_id][emoji]
            del self.rr_data[message_id][emoji]
            
            if not self.rr_data[message_id]:
                del self.rr_data[message_id]
                
            await self.bot.db.save("reaction_roles.json", self.rr_data)
            await interaction.response.send_message(f"✅ Removed reaction role link: {emoji} ➔ {role_name} on message {message_id}.")
        else:
            await interaction.response.send_message("That link doesn't exist.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot: return
        
        msg_id = str(payload.message_id)
        if msg_id in self.rr_data:
            emoji_name = str(payload.emoji.name)
            if payload.emoji.id:
                emoji_name = f"<:{payload.emoji.name}:{payload.emoji.id}>"
            
            role_name = self.rr_data[msg_id].get(emoji_name) or self.rr_data[msg_id].get(str(payload.emoji))
            
            if role_name:
                guild = self.bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name=role_name)
                if role and payload.member:
                    try:
                        await payload.member.add_roles(role)
                    except discord.Forbidden:
                        log.error(f"Cannot add role {role_name} for reaction role in {guild.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        msg_id = str(payload.message_id)
        if msg_id in self.rr_data:
            emoji_name = str(payload.emoji.name)
            if payload.emoji.id:
                emoji_name = f"<:{payload.emoji.name}:{payload.emoji.id}>"
                
            role_name = self.rr_data[msg_id].get(emoji_name) or self.rr_data[msg_id].get(str(payload.emoji))
            
            if role_name:
                guild = self.bot.get_guild(payload.guild_id)
                role = discord.utils.get(guild.roles, name=role_name)
                member = guild.get_member(payload.user_id)
                if role and member and not member.bot:
                    try:
                        await member.remove_roles(role)
                    except discord.Forbidden:
                        log.error(f"Cannot remove role {role_name} for reaction role in {guild.name}")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
