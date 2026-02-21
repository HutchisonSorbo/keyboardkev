import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

import config
import helpers

log = logging.getLogger("CoachBot.Moderation")

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = helpers.load_json(config.WARNINGS_FILE)
        self.message_cache = {}

    def is_mod(self, member):
        return helpers.has_role(member, config.MOD_ROLE)

    async def log_mod_action(self, guild, action, target, moderator, reason):
        channel = discord.utils.get(guild.text_channels, name=config.MOD_LOG_CHANNEL)
        if not channel:
            return
            
        embed = helpers.format_embed(
            title=f"Mod Action: {action}",
            description=f"**Target:** {target.mention} ({target.name})\n**Moderator:** {moderator}\n**Reason:** {reason}",
            colour=config.COLOUR_MOD
        )
        embed.set_footer(text=f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            log.error(f"Cannot send to mod log channel in {guild.name}")

    async def add_warning(self, member, reason, moderator="AutoMod"):
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
            
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
            
        self.warnings[guild_id][user_id].append({
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "moderator": moderator
        })
        
        helpers.save_json(config.WARNINGS_FILE, self.warnings)
        
        warn_count = len(self.warnings[guild_id][user_id])
        
        await self.log_mod_action(member.guild, "WARNING", member, moderator, reason)
        
        try:
            await member.send(f"You have been warned in {member.guild.name} for: {reason}. You now have {warn_count} warning(s).")
        except discord.Forbidden:
            pass
            
        if warn_count >= config.WARNINGS_BEFORE_BAN:
            await self._auto_ban(member, "Reached maximum warnings (AutoBan)")
        elif warn_count >= config.WARNINGS_BEFORE_KICK:
            await self._auto_kick(member, "Reached kick warning threshold (AutoKick)")

    async def _auto_kick(self, member, reason):
        try:
            await member.kick(reason=reason)
            await self.log_mod_action(member.guild, "KICK", member, "AutoMod", reason)
        except discord.Forbidden:
            log.error(f"Failed to auto-kick {member.name} - permissions error")

    async def _auto_ban(self, member, reason):
        try:
            await member.ban(reason=reason)
            await self.log_mod_action(member.guild, "BAN", member, "AutoMod", reason)
        except discord.Forbidden:
            log.error(f"Failed to auto-ban {member.name} - permissions error")

    @app_commands.command(name="warn", description="Issue a warning to a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    async def warn_command(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        await self.add_warning(member, reason, str(interaction.user))
        await interaction.response.send_message(f"✅ Warned {member.mention} for: {reason}")

    @app_commands.command(name="warnings", description="Show all warnings for a member")
    async def warnings_command(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        user_warnings = self.warnings.get(guild_id, {}).get(user_id, [])
        
        if not user_warnings:
            await interaction.response.send_message(f"{member.mention} has 0 warnings.")
            return
            
        desc = ""
        for i, w in enumerate(user_warnings, 1):
            dt = datetime.fromisoformat(w["timestamp"]).strftime("%Y-%m-%d")
            desc += f"**{i}.** [{dt}] {w['reason']} (by {w['moderator']})\n"
            
        embed = helpers.format_embed(
            title=f"Warnings for {member.name}",
            description=desc,
            colour=config.COLOUR_MOD
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearwarnings", description="Clear a member's warning record (Admin only)")
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)
        
        if guild_id in self.warnings and user_id in self.warnings[guild_id]:
            del self.warnings[guild_id][user_id]
            helpers.save_json(config.WARNINGS_FILE, self.warnings)
            
        await interaction.response.send_message(f"✅ Cleared warnings for {member.mention}.")
        await self.log_mod_action(interaction.guild, "CLEAR WARNINGS", member, str(interaction.user), "Manually cleared record")

    @app_commands.command(name="mute", description="Timeout a member")
    async def mute_command(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        duration = timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f"✅ Muted {member.mention} for {minutes} minutes.")
            await self.log_mod_action(interaction.guild, f"MUTE ({minutes}m)", member, str(interaction.user), reason)
        except discord.Forbidden:
            await interaction.response.send_message("Failed to mute member. Check my role hierarchy.", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member")
    async def kick_command(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role.", ephemeral=True)
            return
            
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ Kicked {member.mention}.")
            await self.log_mod_action(interaction.guild, "KICK", member, str(interaction.user), reason)
        except discord.Forbidden:
            await interaction.response.send_message("Failed to kick member. Check my role hierarchy.", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member")
    async def ban_command(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role.", ephemeral=True)
            return
            
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"✅ Banned {member.mention}.")
            await self.log_mod_action(interaction.guild, "BAN", member, str(interaction.user), reason)
        except discord.Forbidden:
            await interaction.response.send_message("Failed to ban member. Check my role hierarchy.", ephemeral=True)

    @app_commands.command(name="purge", description="Delete recent messages in channel (Admin only)")
    async def purge(self, interaction: discord.Interaction, number: int):
        if not self.is_mod(interaction.user):
            await interaction.response.send_message("You need the Commissioner role.", ephemeral=True)
            return
            
        if number < 1 or number > 100:
            await interaction.response.send_message("Number must be between 1 and 100.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=number)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        if self.is_mod(message.author):
            return

        # Check banned words
        content_lower = message.content.lower()
        content_nospaces = content_lower.replace(" ", "")
        
        for word in config.BANNED_WORDS:
            if word.lower() in content_nospaces:
                try:
                    await message.delete()
                    await self.add_warning(message.author, f"Used banned word pattern.", "AutoMod")
                    return # Stop processing
                except discord.Forbidden:
                    pass

        # Check spam
        now = datetime.now()
        user_id = message.author.id
        
        if user_id not in self.message_cache:
            self.message_cache[user_id] = []
            
        # Add current message timestamp
        self.message_cache[user_id].append(now)
        
        # Clean up old messages outside window
        window_start = now - timedelta(seconds=config.SPAM_TIME_WINDOW_SECONDS)
        self.message_cache[user_id] = [t for t in self.message_cache[user_id] if t > window_start]
        
        if len(self.message_cache[user_id]) > config.SPAM_MESSAGE_THRESHOLD:
            # SPAM DETECTED
            self.message_cache[user_id] = [] # Clear so we don't spam the mute
            try:
                duration = timedelta(minutes=config.AUTO_MUTE_MINUTES)
                await message.author.timeout(duration, reason="AutoMod: Spam detected")
                await self.add_warning(message.author, "Spamming channel (AutoMuted)", "AutoMod")
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))
