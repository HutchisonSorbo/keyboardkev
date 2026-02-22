import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime

import config
import helpers

log = logging.getLogger("CoachBot.KeeperDeadlines")

class KeeperDeadlines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deadlines = {}

    async def cog_load(self):
        self.deadlines = await self.bot.db.load("deadlines.json")

    @app_commands.command(name="deadlines", description="View upcoming league deadlines")
    async def view_deadlines(self, interaction: discord.Interaction):
        if not self.deadlines:
            await interaction.response.send_message("No upcoming deadlines configured. Relax and grab a pint.", ephemeral=True)
            return
            
        embed = discord.Embed(title="⏰ Upcoming League Deadlines", color=config.COLOUR_DRAFT)
        
        has_future = False
        now = datetime.now()
        
        for name, date_str in self.deadlines.items():
            dt = datetime.fromisoformat(date_str)
            if dt > now:
                has_future = True
                days_left = (dt - now).days
                hours_left = int((dt - now).seconds / 3600)
                
                time_str = f"{days_left} days, {hours_left} hours" if days_left > 0 else f"{hours_left} hours"
                
                embed.add_field(
                    name=name, 
                    value=f"**{dt.strftime('%d %b %Y, %I:%M %p')}**\nTime remaining: *{time_str}*", 
                    inline=False
                )
                
        if not has_future:
             await interaction.response.send_message("All deadlines have passed. The season is in full swing.", ephemeral=True)
             return
             
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setdeadline", description="Set a league deadline (Admin)")
    @app_commands.describe(name="Name of the deadline (e.g., 'List Lodgement')", date="Format: YYYY-MM-DD HH:MM (24h time)")
    async def set_deadline(self, interaction: discord.Interaction, name: str, date: str):
        if not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need Commissioner permissions to set deadlines.", ephemeral=True)
            return

        try:
            dt = datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use `YYYY-MM-DD HH:MM` (e.g. `2027-02-15 18:00`).", ephemeral=True)
            return
            
        self.deadlines[name] = dt.isoformat()
        await self.bot.db.save("deadlines.json", self.deadlines)
        
        await interaction.response.send_message(f"✅ Deadline **'{name}'** set for **{dt.strftime('%d %B %Y at %I:%M %p')}**.")

    @app_commands.command(name="cleardeadline", description="Remove a league deadline (Admin)")
    @app_commands.describe(name="Exact name of the deadline to remove")
    async def clear_deadline(self, interaction: discord.Interaction, name: str):
        if not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need Commissioner permissions to remove deadlines.", ephemeral=True)
            return
            
        if name in self.deadlines:
            del self.deadlines[name]
            await self.bot.db.save("deadlines.json", self.deadlines)
            await interaction.response.send_message(f"✅ Removed deadline '{name}'.")
        else:
            await interaction.response.send_message(f"Deadline '{name}' not found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(KeeperDeadlines(bot))
