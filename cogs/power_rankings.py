import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
import json
import os

import config
import helpers

log = logging.getLogger("CoachBot.PowerRankings")


class PowerRankings(commands.Cog):
    """Kev's weekly power rankings — uses Gemini AI to rank all 8 coaches
    based on roster data, matchup results, and form."""

    def __init__(self, bot):
        self.bot = bot
        self.last_rankings_round = None
        self.power_rankings_loop.start()

    def cog_unload(self):
        self.power_rankings_loop.cancel()

    # -------------------------------------------------------------------------
    # Data gathering
    # -------------------------------------------------------------------------

    def get_roster_data(self):
        """Load scraped rosters from disk."""
        try:
            with open("data/rosters.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    async def scrape_league_standings(self):
        """Scrape the Keeper Fantasy league page for standings and matchup data."""
        league_id = getattr(config, 'KEEPER_LEAGUE_ID', None)
        if not league_id:
            return None

        url = f"https://keeperfantasy.com/afl/{league_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
        except Exception as e:
            log.error(f"Error fetching league page for power rankings: {e}")
            return None

        soup = BeautifulSoup(html, 'html.parser')
        teams = []

        # Extract team names and records from the league page
        for link in soup.find_all('a', href=lambda h: h and '/matchup?' in h):
            text = link.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            for i, line in enumerate(lines):
                # Records follow the pattern X-X-X
                if '-' in line and line.count('-') == 2:
                    parts = line.split('-')
                    if all(p.strip().isdigit() for p in parts):
                        # The line before is the team name
                        if i > 0:
                            team_name = lines[i - 1]
                            wins, losses, draws = [int(p.strip()) for p in parts]
                            # Check we haven't added this team yet
                            if not any(t["name"] == team_name for t in teams):
                                # Look for a score after the record
                                score = 0
                                projected = 0
                                for j in range(i + 1, min(i + 3, len(lines))):
                                    if lines[j].isdigit():
                                        if score == 0:
                                            score = int(lines[j])
                                        else:
                                            projected = int(lines[j])
                                            break

                                teams.append({
                                    "name": team_name,
                                    "wins": wins,
                                    "losses": losses,
                                    "draws": draws,
                                    "score": score,
                                    "projected": projected
                                })

        return teams if teams else None

    # -------------------------------------------------------------------------
    # Gemini AI power rankings generation
    # -------------------------------------------------------------------------

    async def generate_rankings(self, standings, rosters):
        """Use Gemini AI to generate power rankings."""
        # Check if the KnowledgeBase cog is loaded (has the Gemini client)
        kb_cog = self.bot.get_cog("KnowledgeBase")
        if not kb_cog or not kb_cog.client_ready:
            log.warning("Gemini AI not available for power rankings")
            return None

        tz = pytz.timezone(config.TIMEZONE)
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        roster_summary = ""
        if rosters:
            for team, players in rosters.items():
                roster_summary += f"\n{team}: {', '.join(players[:10])}"
                if len(players) > 10:
                    roster_summary += f" (+{len(players) - 10} more)"

        standings_text = ""
        if standings:
            for t in standings:
                standings_text += f"\n{t['name']}: {t['wins']}W-{t['losses']}L-{t['draws']}D | Score: {t['score']} | Projected: {t['projected']}"

        prompt = f"""[SYSTEM: Current date and time is {current_time}. You are generating weekly Power Rankings for the Keyboard Coaches fantasy league.]

LEAGUE STANDINGS:{standings_text if standings_text else " No standings data available yet."}

TEAM ROSTERS:{roster_summary if roster_summary else " No roster data available yet."}

Generate power rankings for all 8 teams in the Keyboard Coaches league. For each team (ranked 1 to 8):
1. Give a brief, sharp assessment (2-3 sentences max per team)
2. Focus on roster strength, recent form, upcoming matchups, and any key risks
3. Use your Warnie persona — direct, opinionated, data-driven
4. If it's pre-season or Round 1, base rankings on roster quality and projected totals

Format each ranking as:
**#1. Team Name** ⬆️/⬇️/➡️ (movement indicator)
Assessment text here.

Keep the entire response under 2000 characters for Discord embed limits."""

        try:
            response = await kb_cog._generate(prompt)
            return response
        except Exception as e:
            log.error(f"Gemini AI error generating power rankings: {e}")
            return None

    # -------------------------------------------------------------------------
    # Slash command: /powerrankings
    # -------------------------------------------------------------------------

    @app_commands.command(name="powerrankings", description="Get Kev's weekly power rankings of all 8 coaches")
    async def power_rankings_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        standings = await self.scrape_league_standings()
        rosters = self.get_roster_data()

        rankings_text = await self.generate_rankings(standings, rosters)

        if not rankings_text:
            await interaction.followup.send(
                "Can't generate power rankings right now. Either the AI isn't ready or the league data is unavailable."
            )
            return

        embed = discord.Embed(
            title="📊 Kev's Power Rankings",
            description=rankings_text[:4000],
            colour=config.COLOUR_AFL
        )
        embed.set_footer(text="Power Rankings | Keyboard Kev | Updated Weekly")
        await interaction.followup.send(embed=embed)

    # -------------------------------------------------------------------------
    # Scheduled auto-post — Wednesday 12 PM
    # -------------------------------------------------------------------------

    @tasks.loop(minutes=30)
    async def power_rankings_loop(self):
        """Post power rankings to #afl-fantasy on Wednesday midday."""
        try:
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)

            # Wednesday at 12 PM
            if now.weekday() != 2 or now.hour != 12 or now.minute >= 30:
                return

            # Simple guard against double-posting
            week_key = f"{now.year}-W{now.isocalendar()[1]}"
            if self.last_rankings_round == week_key:
                return

            standings = await self.scrape_league_standings()
            rosters = self.get_roster_data()
            rankings_text = await self.generate_rankings(standings, rosters)

            if not rankings_text:
                return

            self.last_rankings_round = week_key

            embed = discord.Embed(
                title="📊 Kev's Power Rankings",
                description=rankings_text[:4000],
                colour=config.COLOUR_AFL
            )
            embed.set_footer(text="Power Rankings | Keyboard Kev | Updated Weekly")

            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=config.AFL_CHANNEL)
                if channel:
                    try:
                        await channel.send(embed=embed)
                        log.info("Posted power rankings to #afl-fantasy")
                    except discord.Forbidden:
                        log.error(f"Missing permissions for #{config.AFL_CHANNEL} in {guild.name}")

        except Exception as e:
            log.error(f"Error in power rankings loop: {e}")

    @power_rankings_loop.before_loop
    async def before_power_rankings(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(PowerRankings(bot))
