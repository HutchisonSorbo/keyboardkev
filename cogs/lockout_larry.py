import discord
from discord.ext import commands, tasks
import pytz
from zoneinfo import ZoneInfo
from datetime import datetime, time, timedelta
import logging
import aiohttp

import config

log = logging.getLogger("CoachBot.LockoutLarry")

class LockoutLarry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tz = pytz.timezone(config.TIMEZONE)
        
        # Use ZoneInfo for discord.ext.tasks.loop to avoid historical offset bugs
        self.zone_info = ZoneInfo(config.TIMEZONE)
        
        self.wednesday_time = time(hour=config.WEDNESDAY_REMINDER_HOUR, minute=config.WEDNESDAY_REMINDER_MINUTE, tzinfo=self.zone_info)
        self.thursday_time = time(hour=config.THURSDAY_REMINDER_HOUR, minute=config.THURSDAY_REMINDER_MINUTE, tzinfo=self.zone_info)
        
        self.wednesday_announcement.start()
        self.thursday_announcement.start()

    def cog_unload(self):
        self.wednesday_announcement.cancel()
        self.thursday_announcement.cancel()

    async def get_upcoming_games(self):
        url = f"{config.SQUIGGLE_BASE_URL}?q=games;year={datetime.now(self.tz).year}"
        headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("games", [])
        except Exception as e:
            log.error(f"Failed to fetch games from Squiggle: {e}")
        return []

    @tasks.loop(time=[time(hour=config.WEDNESDAY_REMINDER_HOUR, minute=config.WEDNESDAY_REMINDER_MINUTE, tzinfo=ZoneInfo(config.TIMEZONE))])
    async def wednesday_announcement(self):
        # We only want to send this on Wednesdays.
        now = datetime.now(self.tz)
        if now.weekday() == 2: # 0=Mon, 2=Wed
            # Check if there's a Thursday game
            games = await self.get_upcoming_games()
            has_thursday_game = False
            for game in games:
                game_time_str = game.get("localtime")
                if not game_time_str:
                    continue
                try:
                    game_dt = datetime.strptime(game_time_str, "%Y-%m-%d %H:%M:%S")
                    game_dt = self.tz.localize(game_dt)
                    # if the game is in the future within 8 days and on a Thursday
                    if now < game_dt < now + timedelta(days=8) and game_dt.weekday() == 3:
                        has_thursday_game = True
                        break
                except ValueError:
                    continue
                    
            if has_thursday_game:
                await self._send_reminder(config.WEDNESDAY_REMINDER_MESSAGE)
                log.info("Wednesday reminder sent (Game on Thursday).")
            else:
                log.info("No Thursday game found. Wednesday reminder skipped.")

    @tasks.loop(time=[time(hour=config.THURSDAY_REMINDER_HOUR, minute=config.THURSDAY_REMINDER_MINUTE, tzinfo=ZoneInfo(config.TIMEZONE))])
    async def thursday_announcement(self):
        # We only want to send this on Thursdays.
        now = datetime.now(self.tz)
        if now.weekday() == 3: # 0=Mon, 3=Thu
            # Check if there's a Friday, Saturday or Sunday game
            games = await self.get_upcoming_games()
            has_weekend_game = False
            for game in games:
                game_time_str = game.get("localtime")
                if not game_time_str:
                    continue
                try:
                    game_dt = datetime.strptime(game_time_str, "%Y-%m-%d %H:%M:%S")
                    game_dt = self.tz.localize(game_dt)
                    # if the game is in the future within 7 days and on a Fri(4), Sat(5) or Sun(6)
                    if now < game_dt < now + timedelta(days=7) and game_dt.weekday() in [4, 5, 6]:
                        has_weekend_game = True
                        break
                except ValueError:
                    continue
            
            if has_weekend_game:
                await self._send_reminder(config.THURSDAY_REMINDER_MESSAGE)
                log.info("Thursday reminder sent (Weekend games found).")
            else:
                log.info("No weekend games found. Thursday reminder skipped.")

    @wednesday_announcement.before_loop
    @thursday_announcement.before_loop
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
