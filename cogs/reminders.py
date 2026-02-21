import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
import asyncio
import uuid

import config
import helpers

log = logging.getLogger("CoachBot.Reminders")

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        data = helpers.load_json("data/reminders.json")
        self.reminders = data.get("reminders", {})
        self.reminder_check.start()

    def cog_unload(self):
        self.reminder_check.cancel()

    def parse_time(self, time_str):
        unit = time_str[-1].lower()
        try:
            val = int(time_str[:-1])
        except ValueError:
            return None
            
        if unit == 'm':
            return timedelta(minutes=val)
        elif unit == 'h':
            return timedelta(hours=val)
        elif unit == 'd':
            return timedelta(days=val)
        return None

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        now = datetime.now()
        to_delete = []
        
        for r_id, r_data in list(self.reminders.items()):
            fire_time = datetime.fromisoformat(r_data["fire_time"])
            if now >= fire_time:
                user_id = int(r_data["user_id"])
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                if user:
                    message = r_data["message"]
                    embed = helpers.format_embed(
                        title="⏰ Reminder",
                        description=message,
                        colour=config.COLOUR_REMINDER
                    )
                    
                    if (now - fire_time).total_seconds() > 300: # Over 5 minutes late
                        embed.set_footer(text="Sorry this is late! I was offline.")
                        
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        log.info(f"Could not send reminder to {user.name}")
                        
                to_delete.append(r_id)
                
        if to_delete:
            for r_id in to_delete:
                del self.reminders[r_id]
            helpers.save_json("data/reminders.json", {"reminders": self.reminders})

    @reminder_check.before_loop
    async def before_reminder_check(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        to_delete = []
        # Check immediately on boot if any were missed
        for r_id, r_data in list(self.reminders.items()):
            fire_time = datetime.fromisoformat(r_data["fire_time"])
            if now >= fire_time:
                user_id = int(r_data["user_id"])
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        embed = helpers.format_embed(
                            title="⏰ Late Reminder",
                            description=f"{r_data['message']}\n\n*This reminder is late because I was offline when it was scheduled.*",
                            colour=config.COLOUR_REMINDER
                        )
                        await user.send(embed=embed)
                except Exception as e:
                    log.error(f"Failed late reminder: {e}")
                to_delete.append(r_id)
                
        if to_delete:
            for r_id in to_delete:
                del self.reminders[r_id]
            helpers.save_json("data/reminders.json", {"reminders": self.reminders})


    @app_commands.command(name="remindme", description="Set a personal reminder")
    @app_commands.describe(time="Format: 30m, 2h, 1d", message="What to remind you about")
    async def remindme(self, interaction: discord.Interaction, time: str, message: str):
        delta = self.parse_time(time)
        if not delta:
            await interaction.response.send_message("Invalid time format. Use something like `30m`, `2h`, or `1d`.", ephemeral=True)
            return
            
        if delta.total_seconds() > config.MAX_REMINDER_HOURS * 3600:
            await interaction.response.send_message(f"Reminders cannot be longer than {config.MAX_REMINDER_HOURS} hours.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        active_count = sum(1 for r in self.reminders.values() if r["user_id"] == user_id)
        if active_count >= config.MAX_REMINDERS_PER_USER:
            await interaction.response.send_message(f"You have reached the maximum of {config.MAX_REMINDERS_PER_USER} active reminders.", ephemeral=True)
            return
            
        fire_time = datetime.now() + delta
        r_id = str(uuid.uuid4())[:8]
        
        message = message.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        
        self.reminders[r_id] = {
            "user_id": user_id,
            "fire_time": fire_time.isoformat(),
            "message": message
        }
        
        helpers.save_json("data/reminders.json", {"reminders": self.reminders})
        
        await interaction.response.send_message(f"✅ I will remind you about that in **{time}**.", ephemeral=True)

    @app_commands.command(name="myreminders", description="List your active reminders")
    async def myreminders(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_reminders = {k: v for k, v in self.reminders.items() if v["user_id"] == user_id}
        
        if not user_reminders:
            await interaction.response.send_message("You don't have any active reminders.", ephemeral=True)
            return
            
        desc = ""
        for r_id, r_data in user_reminders.items():
            dt = datetime.fromisoformat(r_data["fire_time"]).strftime("%Y-%m-%d %H:%M")
            desc += f"**ID: `{r_id}`** - Fires at: {dt}\n_{r_data['message']}_\n\n"
            
        embed = helpers.format_embed("Your Active Reminders", desc[:4000], config.COLOUR_REMINDER)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cancelreminder", description="Cancel a reminder by ID")
    async def cancelreminder(self, interaction: discord.Interaction, reminder_id: str):
        user_id = str(interaction.user.id)
        
        if reminder_id in self.reminders and self.reminders[reminder_id]["user_id"] == user_id:
            del self.reminders[reminder_id]
            helpers.save_json("data/reminders.json", {"reminders": self.reminders})
            await interaction.response.send_message(f"✅ Cancelled reminder `{reminder_id}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"Reminder `{reminder_id}` not found or doesn't belong to you.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reminders(bot))
