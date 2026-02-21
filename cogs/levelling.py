import discord
from discord import app_commands
from discord.ext import commands
import logging
import math
import time

import config
import helpers

log = logging.getLogger("CoachBot.Levelling")

class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = helpers.load_json(config.XP_DATA_FILE)
        self.cooldowns = {} # user_id -> timestamp

    def get_level_from_xp(self, xp):
        # level = int(0.1 * sqrt(xp))
        if xp <= 0: return 0
        return int(0.1 * math.sqrt(xp))
        
    def get_xp_for_level(self, level):
        # xp = (level / 0.1) ^ 2 = (level * 10) ^ 2 = level^2 * 100
        return (level * 10) ** 2

    @commands.Cog.listener()
    async def on_message(self, message):
        if not config.LEVELLING_ENABLED: return
        if message.author.bot or not message.guild: return
        
        # Check prefix/commands (don't give XP for commands)
        if message.content.startswith(config.PREFIX) or message.content.startswith('/'): return
        
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        
        # Cooldown check
        now = time.time()
        if user_id in self.cooldowns:
            if now - self.cooldowns[user_id] < config.XP_COOLDOWN_SECONDS:
                return
        
        self.cooldowns[user_id] = now
        
        if guild_id not in self.xp_data:
            self.xp_data[guild_id] = {}
            
        if user_id not in self.xp_data[guild_id]:
            self.xp_data[guild_id][user_id] = 0
            
        old_level = self.get_level_from_xp(self.xp_data[guild_id][user_id])
        self.xp_data[guild_id][user_id] += config.XP_PER_MESSAGE
        new_level = self.get_level_from_xp(self.xp_data[guild_id][user_id])
        
        # Save every message
        helpers.save_json(config.XP_DATA_FILE, self.xp_data)
        
        if new_level > old_level:
            await self.handle_level_up(message.author, new_level)

    async def handle_level_up(self, member, new_level):
        # Assign role rewards
        reward_role_name = config.LEVEL_ROLE_REWARDS.get(str(new_level)) or config.LEVEL_ROLE_REWARDS.get(new_level)
        if reward_role_name:
            role = discord.utils.get(member.guild.roles, name=reward_role_name)
            if role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    log.error(f"Failed to give level reward role {reward_role_name} to {member.name}")

        # Send message
        msg_text = config.LEVEL_UP_MESSAGE.format(member=member.mention, level=new_level)
        
        if config.LEVEL_UP_CHANNEL:
            channel = discord.utils.get(member.guild.text_channels, name=config.LEVEL_UP_CHANNEL)
            if channel:
                # Wrap in embed for style
                embed = discord.Embed(description=msg_text, color=config.COLOUR_LEVEL)
                await channel.send(embed=embed)
        else:
            try:
                await member.send(msg_text)
            except discord.Forbidden:
                pass

    @app_commands.command(name="rank", description="Check your XP and level")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        if not config.LEVELLING_ENABLED:
            await interaction.response.send_message("Levelling is disabled.", ephemeral=True)
            return
            
        member = member or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        xp = self.xp_data.get(guild_id, {}).get(user_id, 0)
        level = self.get_level_from_xp(xp)
        next_xp = self.get_xp_for_level(level + 1)
        
        # Calculate rank
        server_users = self.xp_data.get(guild_id, {})
        rank_pos = 1
        for uid, uxp in server_users.items():
            if uxp > xp:
                rank_pos += 1
                
        embed = helpers.format_embed(
            title=f"{member.name}'s Rank",
            description=f"**Level {level}**\nXP: {xp} / {next_xp}\nServer Rank: #{rank_pos}",
            colour=config.COLOUR_LEVEL
        )
        embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Top 10 members by XP")
    async def leaderboard(self, interaction: discord.Interaction):
        if not config.LEVELLING_ENABLED:
            await interaction.response.send_message("Levelling is disabled.", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        server_users = self.xp_data.get(guild_id, {})
        
        if not server_users:
            await interaction.response.send_message("No one has any XP yet.")
            return
            
        sorted_users = sorted(server_users.items(), key=lambda x: x[1], reverse=True)[:10]
        
        description = ""
        for i, (uid, xp) in enumerate(sorted_users, 1):
            member = interaction.guild.get_member(int(uid))
            name = member.name if member else f"Unknown User ({uid})"
            level = self.get_level_from_xp(xp)
            description += f"**{i}.** {name} - Level {level} ({xp} XP)\n"
            
        embed = helpers.format_embed(
            title="XP Leaderboard",
            description=description,
            colour=config.COLOUR_LEVEL
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetxp", description="Reset a member's XP (Admin only)")
    async def resetxp(self, interaction: discord.Interaction, member: discord.Member):
        if not helpers.has_role(interaction.user, config.MOD_ROLE) and not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        if guild_id in self.xp_data and user_id in self.xp_data[guild_id]:
            self.xp_data[guild_id][user_id] = 0
            helpers.save_json(config.XP_DATA_FILE, self.xp_data)
            
        await interaction.response.send_message(f"✅ Reset XP for {member.mention}.")

async def setup(bot):
    await bot.add_cog(Levelling(bot))
