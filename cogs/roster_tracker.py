import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz

import config
import helpers

log = logging.getLogger("CoachBot.RosterTracker")

class RosterTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rosters = {}
        self.roster_scrape_loop.start()

    def cog_unload(self):
        self.roster_scrape_loop.cancel()

    async def scrape_rosters(self):
        """Web scrapes the keeper fantasy league to get live owner rosters."""
        league_id = getattr(config, 'KEEPER_LEAGUE_ID', None)
        if not league_id:
            log.warning("KEEPER_LEAGUE_ID not set in config. Cannot scrape rosters.")
            return False

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        scraped_data = {}
        
        # We loop exactly config.TOTAL_TEAMS (default 8)
        for team_idx in range(1, config.TOTAL_TEAMS + 1):
            url = f"https://keeperfantasy.com/afl/{league_id}/{team_idx}"
            try:
                async with self.bot.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find the team name using the title or header
                        title_tag = soup.find('title')
                        team_name = f"Team {team_idx}"
                        if title_tag and "-" in title_tag.text:
                            # Usually "Lineup - Team Name - Keeper"
                            parts = title_tag.text.split("-")
                            if len(parts) >= 2:
                                team_name = parts[1].strip()

                        players = []
                        # Look for all rows that might contain player data
                        for tr in soup.find_all('tr'):
                            # A simple heuristic: player rows usually have an <a> tag pointing to /player/
                            player_link = tr.find('a', href=lambda href: href and '/player/' in href)
                            if player_link:
                                player_name = player_link.text.strip()
                                if player_name and player_name != "- empty -":
                                    players.append(player_name)
                                    
                        # Since the draft hasn't happened yet, we might fallback to checking tds 
                        if not players:
                            for td in soup.find_all('td'):
                                text = td.get_text(strip=True)
                                # Basic heuristic of an afl player name vs random stats
                                if len(text) > 4 and "-" not in text and not text.isdigit() and text != "empty":
                                    # Very basic fallback
                                    pass
                                    
                        scraped_data[team_name] = players
                        log.info(f"Scraped {len(players)} players for {team_name}")
                        
            except Exception as e:
                log.error(f"Error scraping team {team_idx}: {e}")

        if scraped_data:
            self.rosters = scraped_data
            try:
                os.makedirs("data", exist_ok=True)
                with open("data/rosters.json", "w") as f:
                    json.dump(self.rosters, f, indent=4)
                log.info("Successfully saved scraped rosters to data/rosters.json")
                return True
            except Exception as e:
                log.error(f"Error saving rosters.json: {e}")
                
        return False

    @tasks.loop(minutes=1)
    async def roster_scrape_loop(self):
        try:
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)
            
            # Scrape at exactly 9:00 AM AEDT on Tuesday (1) and Friday (4)
            if now.weekday() in [1, 4] and now.hour == 9 and now.minute == 0:
                log.info("Starting scheduled twice-weekly roster scrape.")
                await self.scrape_rosters()
                
        except Exception as e:
            log.error(f"Error in roster scrape loop: {e}")

    @roster_scrape_loop.before_loop
    async def before_roster_scrape_loop(self):
        await self.bot.wait_until_ready()
        # On boot, try to load from disk
        try:
            with open("data/rosters.json", "r") as f:
                self.rosters = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.rosters = {}

    @app_commands.command(name="force_scrape", description="Manually trigger a roster scrape (Admin)")
    async def force_scrape(self, interaction: discord.Interaction):
        if not helpers.has_role(interaction.user, getattr(config, 'DRAFT_ADMIN_ROLE', 'Commissioner')):
            await interaction.response.send_message("Only the Commissioner can force a scrape.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        success = await self.scrape_rosters()
        if success:
            team_count = len(self.rosters)
            player_count = sum(len(p) for p in self.rosters.values())
            await interaction.followup.send(f"✅ Roster scrape complete. Found {player_count} players across {team_count} teams. The AI Knowledge Base has been updated.")
        else:
            await interaction.followup.send("❌ Scrape failed. Check bot console logs.")

async def setup(bot):
    await bot.add_cog(RosterTracker(bot))
