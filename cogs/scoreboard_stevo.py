import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime
import asyncio

import config
import helpers

log = logging.getLogger("CoachBot.ScoreboardStevo")

class ScoreboardStevo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = helpers.SimpleCache()
        self.completed_games = set()
        self.live_score_check.start()
        
    def cog_unload(self):
        self.live_score_check.cancel()

    async def fetch_squiggle(self, endpoint, params=None):
        url = f"{config.SQUIGGLE_BASE_URL}?q={endpoint}"
        if params:
            for k, v in params.items():
                url += f"&{k}={v}"
                
        cached = self.cache.get(url)
        if cached:
            return cached
            
        headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
        
        try:
            async with self.bot.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache.set(url, data, config.API_CACHE_TTL_SECONDS)
                    return data
                else:
                    log.error(f"Squiggle API error: {response.status} for {url}")
                    return None
        except Exception as e:
            log.error(f"Exception fetching Squiggle: {e}")
            return None

    def in_allowed_channel(self, interaction: discord.Interaction):
        if config.ALLOWED_COMMAND_CHANNELS and interaction.channel.name not in config.ALLOWED_COMMAND_CHANNELS:
            return False
        return True

    @app_commands.command(name="scores", description="Get current round AFL scores")
    async def scores(self, interaction: discord.Interaction):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        data = await self.fetch_squiggle("games", {"year": datetime.now().year})
        if not data or "games" not in data:
            await interaction.followup.send("Failed to fetch scores from Squiggle API.")
            return
            
        games = data["games"]
        
        current_round = 0
        for g in games:
            if g.get("complete", 100) < 100:
                current_round = g.get("round", 0)
                break
        
        if current_round == 0 and games:
            current_round = games[-1].get("round", 0)
            
        round_games = [g for g in games if g.get("round") == current_round]
        
        if not round_games:
            await interaction.followup.send("No games found for the current round.")
            return
            
        embed = discord.Embed(title=f"AFL Round {current_round} Scores", color=config.COLOUR_SCORES)
        
        for g in round_games:
            home = g.get("hteam", "Unknown")
            away = g.get("ateam", "Unknown")
            hscore = g.get("hscore", 0)
            ascore = g.get("ascore", 0)
            status = g.get("complete", 0)
            
            if status == 100:
                status_text = "FINAL"
            elif status == 0:
                dt = g.get("date", "")
                status_text = f"UPCOMING ({dt})"
            else:
                status_text = f"IN PROGRESS ({status}%)"
                
            embed.add_field(
                name=f"{home} vs {away}",
                value=f"{home} **{hscore}** - {away} **{ascore}**\n*{status_text}*",
                inline=False
            )
            
        embed.set_footer(text="Powered by Squiggle API")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="round", description="Get AFL scores for a specific round")
    @app_commands.describe(number="The round number")
    async def specific_round(self, interaction: discord.Interaction, number: int):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        data = await self.fetch_squiggle("games", {"year": datetime.now().year, "round": number})
        
        if not data or "games" not in data or not data["games"]:
            await interaction.followup.send(f"No games found for Round {number}.")
            return
            
        embed = discord.Embed(title=f"AFL Round {number} Scores", color=config.COLOUR_SCORES)
        
        for g in data["games"]:
            home = g.get("hteam", "Unknown")
            away = g.get("ateam", "Unknown")
            hscore = g.get("hscore", 0)
            ascore = g.get("ascore", 0)
            status = g.get("complete", 0)
            
            if status == 100:
                status_text = "FINAL"
            elif status == 0:
                dt = g.get("date", "")
                status_text = f"UPCOMING ({dt})"
            else:
                status_text = f"IN PROGRESS ({status}%)"
                
            embed.add_field(
                name=f"{home} vs {away}",
                value=f"{home} **{hscore}** - {away} **{ascore}**\n*{status_text}*",
                inline=False
            )
            
        embed.set_footer(text="Powered by Squiggle API")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ladder", description="Current AFL Ladder")
    async def ladder(self, interaction: discord.Interaction):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        data = await self.fetch_squiggle("standings", {"year": datetime.now().year})
        
        if not data or "standings" not in data:
            await interaction.followup.send("Failed to fetch ladder from Squiggle API.")
            return
            
        standings = data["standings"]
        standings.sort(key=lambda x: x.get("rank", 99))
        
        embed = discord.Embed(title=f"AFL Ladder {datetime.now().year}", color=config.COLOUR_SCORES)
        
        ladder_text = ""
        for s in standings:
            rank = s.get("rank", 0)
            team = s.get("name", "Unknown")
            pts = s.get("pts", 0)
            pct = s.get("percentage", 0)
            
            ladder_text += f"**{rank}.** {team} - {pts} pts ({pct:.1f}%)\n"
            
        embed.description = ladder_text
        embed.set_footer(text="Powered by Squiggle API")
        
        await interaction.followup.send(embed=embed)

    @tasks.loop(minutes=5)
    async def live_score_check(self):
        try:
            # Need to use raw request bypassing cache so we actually get live updates
            url = f"{config.SQUIGGLE_BASE_URL}?q=games;year={datetime.now().year}"
            headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
            
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()
                
            games = data.get("games", [])
            for g in games:
                game_id = g.get("id")
                # Game is finished when complete == 100
                if g.get("complete", 0) == 100:
                    if game_id not in self.completed_games:
                        # New completed game discovered!
                        self.completed_games.add(game_id)
                        
                        # Don't spam past games on bot startup. Check if it finished very recently. 
                        # We just send to the scores channel if it's new.
                        # We will assume if the set was empty initially, we just bulk add them and skip announcing.
                        if len(self.completed_games) > 1:
                            await self._announce_full_time(g)
                            
        except Exception as e:
            log.error(f"Error checking live scores: {e}")

    @live_score_check.before_loop
    async def before_live_score_check(self):
        await self.bot.wait_until_ready()
        
        # Populate the finished games array silently right now so we don't spam 
        # announcements for games that ended weeks ago when the bot starts up.
        try:
            from datetime import timedelta
            import pytz
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)

            url = f"{config.SQUIGGLE_BASE_URL}?q=games;year={datetime.now().year}"
            headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    games = data.get("games", [])
                    for g in games:
                        if g.get("complete", 0) == 100:
                            game_date_str = g.get("date", "")
                            try:
                                dt = datetime.strptime(game_date_str, "%Y-%m-%d %H:%M:%S")
                                dt = tz.localize(dt)
                                # If game started > 12 hours ago, silently add to completed
                                if now - dt > timedelta(hours=12):
                                    self.completed_games.add(g.get("id"))
                            except ValueError:
                                self.completed_games.add(g.get("id"))
        except Exception as e:
            log.error(f"Failed to prepopulate finished games array: {e}")

    async def _announce_full_time(self, game):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=config.SCORES_CHANNEL)
            if channel:
                home = game.get("hteam", "Unknown")
                away = game.get("ateam", "Unknown")
                hscore = game.get("hscore", 0)
                ascore = game.get("ascore", 0)
                round_num = game.get("round", "Unknown")
                
                embed = discord.Embed(title=f"🚨 FULL TIME (Round {round_num})", color=config.COLOUR_SCORES)
                embed.description = f"**{home}** {hscore} def. **{away}** {ascore}" if hscore > ascore else f"**{away}** {ascore} def. **{home}** {hscore}"
                if hscore == ascore:
                    embed.description = f"**{home}** {hscore} drew with **{away}** {ascore}"
                
                embed.set_footer(text="Live Score Update Engine")
                
                try:
                    await channel.send(embed=embed)
                    log.info(f"Announced FULL TIME: {home} vs {away}")
                except discord.Forbidden:
                    log.error(f"Missing permissions to post fast score format in {guild.name}")

async def setup(bot):
    await bot.add_cog(ScoreboardStevo(bot))
