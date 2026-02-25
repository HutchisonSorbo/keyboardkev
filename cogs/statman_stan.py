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

    async def fetch_fantasy_players(self):
        url = "https://fantasy.afl.com.au/data/afl/players.json"
        cached = self.cache.get(url)
        if cached:
            return cached
            
        headers = {
            "User-Agent": config.SQUIGGLE_USER_AGENT,
            "Accept-Encoding": "gzip"
        }
        
        try:
            async with self.bot.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache.set(url, data, 3600)
                    return data
                else:
                    log.error(f"Fantasy API error: {response.status} for {url}")
                    return None
        except Exception as e:
            log.error(f"Exception fetching Fantasy: {e}")
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
        
        players_data = await self.fetch_fantasy_players()
        if not players_data:
            await interaction.followup.send("Failed to fetch player list from AFL Fantasy.")
            return
            
        player_names = [f'{p.get("first_name")} {p.get("last_name")}' for p in players_data]
        match, score = process.extractOne(player, player_names, scorer=fuzz.token_sort_ratio)
        
        if score < config.FUZZY_MATCH_THRESHOLD:
            await interaction.followup.send(f"Couldn't find a close match for '{player}'. Did you mean '{match}' ({score}% match)? Please check spelling.")
            return
            
        matched_player = next((p for p in players_data if f'{p.get("first_name")} {p.get("last_name")}' == match), None)
        if not matched_player:
            await interaction.followup.send("Error retrieving player data.")
            return
            
        embed = discord.Embed(title=f"Stats for {match}", color=config.COLOUR_STATS)
        stats = matched_player.get("stats", {})
        
        avg = stats.get("avg_points", 0)
        total = stats.get("total_points", 0)
        games = stats.get("games_played", 0)
        high = stats.get("high_score", 0)
        last3 = stats.get("last_3_avg", 0)
        
        # Format the description
        embed.description = f"**Status:** {matched_player.get('status', 'Unknown').title()}"
        
        embed.add_field(name="Season Average", value=f"{avg} pts", inline=True)
        embed.add_field(name="Last 3 Avg", value=f"{last3} pts", inline=True)
        embed.add_field(name="High Score", value=f"{high} pts", inline=True)
        embed.add_field(name="Total Points", value=f"{total} pts (in {games} games)", inline=False)
        
        query = match.replace(' ', '+')
        footywire_url = f"https://www.footywire.com/afl/footy/ft_search_template?search_name={query}"
        embed.add_field(name="More Stats", value=f"[View {match} on Footywire]({footywire_url})", inline=False)
        
        embed.set_footer(text="Powered by AFL Fantasy Data")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="topscorers", description="Top 10 highest averaging players")
    async def topscorers(self, interaction: discord.Interaction):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        await interaction.response.defer()
        players_data = await self.fetch_fantasy_players()
        if not players_data:
            await interaction.followup.send("Failed to fetch player list from AFL Fantasy.")
            return
            
        # Filter out players who haven't played or have 0 avg
        valid_players = [p for p in players_data if p.get("stats", {}).get("avg_points", 0) > 0 and p.get("stats", {}).get("games_played", 0) >= 3]
        valid_players.sort(key=lambda x: x.get("stats", {}).get("avg_points", 0), reverse=True)
        
        top10 = valid_players[:10]
        
        embed = discord.Embed(title="Top 10 Highest Averaging Players", color=config.COLOUR_STATS)
        desc = ""
        for i, p in enumerate(top10, 1):
            name = f"{p.get('first_name')} {p.get('last_name')}"
            avg = p.get("stats", {}).get("avg_points", 0)
            desc += f"**{i}.** {name} - {avg} pts\n"
            
        embed.description = desc
        embed.set_footer(text="Powered by AFL Fantasy Data (Minimum 3 games)")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="compare", description="Compare two players")
    async def compare(self, interaction: discord.Interaction, player1: str, player2: str):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        players_data = await self.fetch_fantasy_players()
        if not players_data:
            await interaction.followup.send("Failed to fetch player list from AFL Fantasy.")
            return
            
        player_names = [f'{p.get("first_name")} {p.get("last_name")}' for p in players_data]
        
        match1, score1 = process.extractOne(player1, player_names, scorer=fuzz.token_sort_ratio)
        match2, score2 = process.extractOne(player2, player_names, scorer=fuzz.token_sort_ratio)
        
        if score1 < config.FUZZY_MATCH_THRESHOLD or score2 < config.FUZZY_MATCH_THRESHOLD:
            await interaction.followup.send(f"Couldn't find close matches. Did you mean '{match1}' and '{match2}'? Please check spelling.")
            return
            
        p1_data = next((p for p in players_data if f'{p.get("first_name")} {p.get("last_name")}' == match1), None)
        p2_data = next((p for p in players_data if f'{p.get("first_name")} {p.get("last_name")}' == match2), None)
        
        embed = discord.Embed(title=f"Comparison: {match1} vs {match2}", color=config.COLOUR_STATS)
        
        def get_stats_str(p_data):
            stats = p_data.get("stats", {})
            return f"Avg: {stats.get('avg_points', 0)}\nLast 3: {stats.get('last_3_avg', 0)}\nGames: {stats.get('games_played', 0)}"
            
        embed.add_field(name=match1, value=get_stats_str(p1_data), inline=True)
        embed.add_field(name=match2, value=get_stats_str(p2_data), inline=True)
        embed.set_footer(text="Powered by AFL Fantasy Data")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatmanStan(bot))
