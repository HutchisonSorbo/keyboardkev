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

log = logging.getLogger("CoachBot.WeeklyWrap")


class WeeklyWrap(commands.Cog):
    """Monday morning wrap-up: scrapes Keeper Fantasy matchup results
    and posts highlights to #afl-fantasy with Kev's commentary."""

    def __init__(self, bot):
        self.bot = bot
        self.last_wrap_round = None
        self.weekly_wrap_loop.start()

    def cog_unload(self):
        self.weekly_wrap_loop.cancel()

    # -------------------------------------------------------------------------
    # Keeper Fantasy scraper — matchup results for a given round
    # -------------------------------------------------------------------------

    async def scrape_matchups(self, round_num=None):
        """Scrape matchup results from Keeper Fantasy league page."""
        league_id = getattr(config, 'KEEPER_LEAGUE_ID', None)
        if not league_id:
            log.warning("KEEPER_LEAGUE_ID not set. Cannot scrape matchups.")
            return None

        # If no round specified, scrape the main page (shows current/latest round)
        if round_num:
            url = f"https://keeperfantasy.com/afl/{league_id}?round={round_num}"
        else:
            url = f"https://keeperfantasy.com/afl/{league_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            async with self.bot.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    log.error(f"Keeper Fantasy returned {resp.status} for matchups")
                    return None
                html = await resp.text()
        except Exception as e:
            log.error(f"Error fetching Keeper Fantasy matchups: {e}")
            return None

        soup = BeautifulSoup(html, 'html.parser')
        matchups = []

        # Find all matchup links — they follow the pattern /matchup?round=X&m=Y
        for link in soup.find_all('a', href=lambda h: h and '/matchup?' in h):
            text = link.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            if len(lines) >= 6:
                # Pattern: TeamA, Record, Score, Projected, "vs", Score, Projected, TeamB, Record
                try:
                    team_a = lines[0]
                    team_a_record = lines[1]
                    team_a_score = int(lines[2]) if lines[2].isdigit() else 0
                    # Find 'vs' separator
                    vs_idx = None
                    for i, l in enumerate(lines):
                        if l.lower() == 'vs':
                            vs_idx = i
                            break

                    if vs_idx is None:
                        continue

                    # Score before vs is team_a's score, score after vs is team_b's
                    team_b_score = int(lines[vs_idx + 1]) if lines[vs_idx + 1].isdigit() else 0
                    team_b = lines[-2] if not lines[-1][0].isdigit() else lines[-1]

                    # Find team B name — it's the last non-record, non-number line
                    team_b_name = None
                    team_b_record = None
                    for l in reversed(lines):
                        if '-' in l and l.count('-') == 2 and any(c.isdigit() for c in l):
                            team_b_record = l
                        elif team_b_name is None and not l.isdigit() and l.lower() != 'vs':
                            team_b_name = l

                    if team_b_name is None:
                        team_b_name = "Unknown"

                    matchups.append({
                        "team_a": team_a,
                        "team_a_score": team_a_score,
                        "team_a_record": team_a_record,
                        "team_b": team_b_name,
                        "team_b_score": team_b_score,
                        "team_b_record": team_b_record or "0-0-0"
                    })
                except (ValueError, IndexError) as e:
                    log.warning(f"Error parsing matchup line: {e}")
                    continue

        return matchups if matchups else None

    # -------------------------------------------------------------------------
    # Build the wrap-up embed
    # -------------------------------------------------------------------------

    def build_wrap_embed(self, matchups, round_num=None):
        """Build the weekly wrap-up embed from matchup results."""
        round_label = f"Round {round_num}" if round_num else "This Week"
        embed = discord.Embed(
            title=f"📋 Weekly Wrap — {round_label}",
            colour=config.COLOUR_AFL
        )

        if not matchups:
            embed.description = "No matchup data available yet. Check back after the round."
            return embed

        # Find highlights
        all_scores = []
        for m in matchups:
            all_scores.append({"team": m["team_a"], "score": m["team_a_score"]})
            all_scores.append({"team": m["team_b"], "score": m["team_b_score"]})

        if not any(s["score"] > 0 for s in all_scores):
            embed.description = "Round hasn't started yet — no scores to wrap up."
            return embed

        # Highest scorer
        top_scorer = max(all_scores, key=lambda x: x["score"])

        # Wooden spoon (lowest)
        wooden_spoon = min(all_scores, key=lambda x: x["score"])

        # Closest match
        closest = min(matchups, key=lambda m: abs(m["team_a_score"] - m["team_b_score"]))
        closest_margin = abs(closest["team_a_score"] - closest["team_b_score"])

        # Biggest blowout
        blowout = max(matchups, key=lambda m: abs(m["team_a_score"] - m["team_b_score"]))
        blowout_margin = abs(blowout["team_a_score"] - blowout["team_b_score"])

        # Results summary
        results_lines = []
        for m in matchups:
            if m["team_a_score"] > m["team_b_score"]:
                results_lines.append(
                    f"🏆 **{m['team_a']}** {m['team_a_score']} def. {m['team_b']} {m['team_b_score']}"
                )
            elif m["team_b_score"] > m["team_a_score"]:
                results_lines.append(
                    f"🏆 **{m['team_b']}** {m['team_b_score']} def. {m['team_a']} {m['team_a_score']}"
                )
            else:
                results_lines.append(
                    f"🤝 **{m['team_a']}** {m['team_a_score']} drew with **{m['team_b']}** {m['team_b_score']}"
                )

        embed.description = "\n".join(results_lines)

        # Highlight fields
        embed.add_field(
            name="🥇 Highest Scorer",
            value=f"**{top_scorer['team']}** — {top_scorer['score']} pts",
            inline=True
        )
        embed.add_field(
            name="🥄 Wooden Spoon",
            value=f"**{wooden_spoon['team']}** — {wooden_spoon['score']} pts",
            inline=True
        )
        embed.add_field(
            name="🔥 Closest Match",
            value=f"**{closest['team_a']}** vs **{closest['team_b']}** — {closest_margin} pt margin",
            inline=False
        )
        embed.add_field(
            name="💀 Biggest Blowout",
            value=f"**{blowout['team_a']}** vs **{blowout['team_b']}** — {blowout_margin} pt margin",
            inline=False
        )

        embed.set_footer(text="Weekly Wrap | Keyboard Kev")
        return embed

    # -------------------------------------------------------------------------
    # Slash command: /wrap
    # -------------------------------------------------------------------------

    @app_commands.command(name="wrap", description="Get the weekly wrap-up of fantasy matchup results")
    @app_commands.describe(round="Round number (defaults to latest)")
    async def wrap_command(self, interaction: discord.Interaction, round: int = None):
        await interaction.response.defer()

        matchups = await self.scrape_matchups(round_num=round)
        embed = self.build_wrap_embed(matchups, round_num=round)
        await interaction.followup.send(embed=embed)

    # -------------------------------------------------------------------------
    # Scheduled auto-post — Monday 9 AM
    # -------------------------------------------------------------------------

    @tasks.loop(minutes=30)
    async def weekly_wrap_loop(self):
        """Post the weekly wrap to #afl-fantasy on Monday morning."""
        try:
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)

            # Monday at 9 AM
            if now.weekday() != 0 or now.hour != 9 or now.minute >= 30:
                return

            # Determine the most recently completed round
            matchups = await self.scrape_matchups()
            if not matchups:
                return

            # Check we haven't already posted for this round
            # Use a simple hash of matchup data to detect new rounds
            round_hash = hash(str([(m["team_a_score"], m["team_b_score"]) for m in matchups]))
            if round_hash == self.last_wrap_round:
                return

            # Check if there are actual scores (not all zeros)
            if not any(m["team_a_score"] > 0 or m["team_b_score"] > 0 for m in matchups):
                return

            self.last_wrap_round = round_hash
            embed = self.build_wrap_embed(matchups)

            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=config.AFL_CHANNEL)
                if channel:
                    try:
                        await channel.send(embed=embed)
                        log.info("Posted weekly wrap to #afl-fantasy")
                    except discord.Forbidden:
                        log.error(f"Missing permissions for #{config.AFL_CHANNEL} in {guild.name}")

        except Exception as e:
            log.error(f"Error in weekly wrap loop: {e}")

    @weekly_wrap_loop.before_loop
    async def before_weekly_wrap(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(WeeklyWrap(bot))
