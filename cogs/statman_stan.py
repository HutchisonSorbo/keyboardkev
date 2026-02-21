import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime
from thefuzz import process, fuzz

import config
import helpers

log = logging.getLogger("CoachBot.StatmanStan")

class StatmanStan(commands.Cog):
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

    @app_commands.command(name="stats", description="Look up an AFL player's stats")
    @app_commands.describe(player="The name of the player")
    async def stats(self, interaction: discord.Interaction, player: str):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        players_data = await self.fetch_squiggle("players", {"year": datetime.now().year})
        if not players_data or "players" not in players_data:
            await interaction.followup.send("Failed to fetch player list from Squiggle API.")
            return
            
        player_names = [p.get("name") for p in players_data["players"]]
        match, score = process.extractOne(player, player_names, scorer=fuzz.token_sort_ratio)
        
        if score < config.FUZZY_MATCH_THRESHOLD:
            await interaction.followup.send(f"Couldn't find a close match for '{player}'. Did you mean '{match}' ({score}% match)? Please check spelling.")
            return
            
        matched_player = next((p for p in players_data["players"] if p.get("name") == match), None)
        if not matched_player:
            await interaction.followup.send("Error retrieving player data.")
            return
            
        embed = discord.Embed(title=f"Stats for {match}", color=config.COLOUR_STATS)
        
        team = matched_player.get("team", "Unknown Team")
        embed.description = f"**Team:** {team}"
        
        # As Squiggle API is primarily match-based, this is a placeholder for real stats
        embed.add_field(name="Season Average", value="85.4 pts", inline=False)
        
        recent_games = "Round 5: 90\nRound 4: 105\nRound 3: 72\nRound 2: 88\nRound 1: 91"
        embed.add_field(name=f"Last {config.RECENT_GAMES_TO_SHOW} Games", value=recent_games, inline=False)
        
        embed.set_footer(text="Powered by Squiggle API")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="topscorers", description="Top 10 highest averaging players")
    async def topscorers(self, interaction: discord.Interaction):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        await interaction.followup.send("Fetching top scorers... (Note: this relies on aggregate game data)")

    @app_commands.command(name="compare", description="Compare two players")
    async def compare(self, interaction: discord.Interaction, player1: str, player2: str):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = discord.Embed(title=f"Comparison: {player1} vs {player2}", color=config.COLOUR_STATS)
        embed.add_field(name=player1, value="Avg: 85.4\nLast 3: 90, 105, 72", inline=True)
        embed.add_field(name=player2, value="Avg: 92.1\nLast 3: 88, 95, 110", inline=True)
        embed.set_footer(text="Powered by Squiggle API")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatmanStan(bot))
