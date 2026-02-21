import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime, time
import logging

import config

log = logging.getLogger("CoachBot.LockoutLarry")

class LockoutLarry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tz = pytz.timezone(config.TIMEZONE)
        
        # We need to construct the expected times.
        self.first_time = time(hour=config.FIRST_REMINDER_HOUR, minute=config.FIRST_REMINDER_MINUTE, tzinfo=self.tz)
        self.final_time = time(hour=config.FINAL_REMINDER_HOUR, minute=config.FINAL_REMINDER_MINUTE, tzinfo=self.tz)
        
        self.first_reminder.start()
        self.final_reminder.start()

    def cog_unload(self):
        self.first_reminder.cancel()
        self.final_reminder.cancel()

    @tasks.loop(time=[time(hour=config.FIRST_REMINDER_HOUR, minute=config.FIRST_REMINDER_MINUTE, tzinfo=pytz.timezone(config.TIMEZONE))])
    async def first_reminder(self):
        # We only want to send this on Thursdays.
        now = datetime.now(self.tz)
        if now.weekday() == 3: # 0=Mon, 3=Thu
            await self._send_reminder(config.FIRST_REMINDER_MESSAGE)
            log.info("First reminder sent.")

    @tasks.loop(time=[time(hour=config.FINAL_REMINDER_HOUR, minute=config.FINAL_REMINDER_MINUTE, tzinfo=pytz.timezone(config.TIMEZONE))])
    async def final_reminder(self):
        now = datetime.now(self.tz)
        if now.weekday() == 3: # 0=Mon, 3=Thu
            await self._send_reminder(config.FINAL_REMINDER_MESSAGE)
            log.info("Final reminder sent.")

    @first_reminder.before_loop
    @final_reminder.before_loop
    async def before_reminders(self):
        await self.bot.wait_until_ready()

    async def _send_reminder(self, message_text):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=config.AFL_CHANNEL)
            if channel:
                msg = message_text
                if config.PING_EVERYONE:
                    msg = f"@everyone\n{msg}"
                try:
                    await channel.send(msg)
                except discord.Forbidden:
                    log.error(f"Missing permissions to send reminder in {guild.name} #{config.AFL_CHANNEL}")
            else:
                log.warning(f"Reminder channel {config.AFL_CHANNEL} not found in {guild.name}")

async def setup(bot):
    await bot.add_cog(LockoutLarry(bot))
