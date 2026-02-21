import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime

import config
import helpers

log = logging.getLogger("CoachBot.ScoreboardStevo")

class ScoreboardStevo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = helpers.SimpleCache()

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

async def setup(bot):
    await bot.add_cog(ScoreboardStevo(bot))
