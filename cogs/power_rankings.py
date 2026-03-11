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
        """Scrape the Keeper Fantasy matchup page for live scores and matchups."""
        league_id = getattr(config, 'KEEPER_LEAGUE_ID', None)
        if not league_id:
            return None

        url = f"https://keeperfantasy.com/afl/{league_id}/matchup"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                html = await resp.read()
                
        except Exception as e:
            log.error(f"Error fetching league page for power rankings: {e}")
            return None

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            matchups = []
            
            # Find the VS dividers inside matchups
            cards = soup.find_all(lambda tag: tag.name == 'div' and tag.text.strip() == 'vs')
            
            for card_vs in cards:
                container = card_vs.parent
                if container:
                    text_lines = [line.strip() for line in container.parent.get_text(separator='\n').split('\n') if line.strip()]
                    
                    m_data = {"team1": "Unknown", "score1": 0, "team2": "Unknown", "score2": 0}
                    
                    links = container.parent.find_all('a')
                    team_names = []
                    for l in links:
                        if 'round=' in l.get('href', ''):
                            team_names.append(l.get_text(strip=True))
                    
                    if len(team_names) >= 2:
                        m_data["team1"] = team_names[0]
                        m_data["team2"] = team_names[1]
                        
                        try:
                            t1_idx = text_lines.index(team_names[0])
                            # The score is usually 2 spots after the team name (TeamName, "0", SCORE...)
                            m_data["score1"] = int(text_lines[t1_idx + 2])
                        except (ValueError, IndexError):
                            pass

                        try:
                            t2_idx = text_lines.index(team_names[1])
                            m_data["score2"] = int(text_lines[t2_idx + 2])
                        except (ValueError, IndexError):
                            pass
                            
                    matchups.append(m_data)

            return matchups if matchups else None
        except Exception as e:
            log.error(f"Error parsing matchup page: {e}")
            return None

    # -------------------------------------------------------------------------
    # Gemini AI power rankings generation
    # -------------------------------------------------------------------------

    async def generate_rankings(self, matchups, rosters):
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

        matchups_text = ""
        if matchups:
            for m in matchups:
                matchups_text += f"\nMatchup: {m['team1']} (Score: {m['score1']}) vs {m['team2']} (Score: {m['score2']})"

        prompt = f"""[SYSTEM: Current date and time is {current_time}. You are generating weekly Power Rankings for the Keyboard Coaches fantasy league.]

LIVE MATCHUPS & SCORES:{matchups_text if matchups_text else " No live matchups available."}

TEAM ROSTERS:{roster_summary if roster_summary else " No roster data available yet."}

Generate power rankings for all 8 teams in the Keyboard Coaches league. For each team (ranked 1 to 8):
1. Give a brief, sharp assessment (2-3 sentences max per team)
2. Focus on roster strength, this week's live scores, who they are playing this week, and any key risks
3. Use your Warnie persona — direct, opinionated, data-driven. Banter them about their current matchup.
4. If it's pre-season or Round 1, base rankings heavily on their live score performance so far.

Format each ranking as:
**#1. Team Name** ⬆️/⬇️/➡️ (movement indicator)
Assessment text here (including matchup banter).

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

        matchups = await self.scrape_league_standings()
        rosters = self.get_roster_data()

        rankings_text = await self.generate_rankings(matchups, rosters)

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

    @app_commands.command(name="force_rankings", description="Admin: Force generate and post the power rankings immediately")
    @app_commands.checks.has_role("Commissioner")
    async def force_rankings_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        matchups = await self.scrape_league_standings()
        rosters = self.get_roster_data()

        rankings_text = await self.generate_rankings(matchups, rosters)

        if not rankings_text:
            await interaction.followup.send("Failed to generate power rankings.")
            return

        embed = discord.Embed(
            title="📊 Kev's Power Rankings",
            description=rankings_text[:4000],
            colour=config.COLOUR_AFL
        )
        embed.set_footer(text="Power Rankings | Keyboard Kev | Updated Weekly")

        guild = interaction.guild
        channel = discord.utils.get(guild.text_channels, name=config.AFL_CHANNEL)
        if channel:
            await channel.send(embed=embed)
            await interaction.followup.send("Posted Power Rankings to the channel.")
        else:
            await interaction.followup.send("Could not find afl-fantasy channel.")

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

            matchups = await self.scrape_league_standings()
            rosters = self.get_roster_data()
            rankings_text = await self.generate_rankings(matchups, rosters)

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
