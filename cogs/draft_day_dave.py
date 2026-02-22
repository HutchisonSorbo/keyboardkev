import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.DraftDayDave")

class DraftDayDave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.draft_config = {}

    async def cog_load(self):
        self.draft_config = await self.bot.db.load(config.DRAFT_CONFIG_FILE)
        
        if "teams" not in self.draft_config:
            self.draft_config["teams"] = config.DEFAULT_TEAMS
            await self.bot.db.save(config.DRAFT_CONFIG_FILE, self.draft_config)

    def in_allowed_channel(self, interaction: discord.Interaction):
        if config.ALLOWED_COMMAND_CHANNELS and interaction.channel.name not in config.ALLOWED_COMMAND_CHANNELS:
            return False
        return True

    def generate_draft_order(self):
        order = []
        teams = self.draft_config["teams"]
        for round_num in range(1, config.TOTAL_ROUNDS + 1):
            if round_num % 2 != 0:
                round_order = list(range(1, config.TOTAL_TEAMS + 1))
            else:
                round_order = list(range(config.TOTAL_TEAMS, 0, -1))
            
            for pick_in_round in round_order:
                order.append({
                    "round": round_num,
                    "team_slot": pick_in_round,
                    "team_name": teams[pick_in_round - 1]
                })
        return order

    @app_commands.command(name="draftorder", description="Full snake draft order")
    async def draftorder(self, interaction: discord.Interaction):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return

        order = self.generate_draft_order()
        
        embed = discord.Embed(title="🐍 Snake Draft Order", color=config.COLOUR_DRAFT)
        
        description = "Showing first 5 rounds. Use `/currentpick` or `/mypicks` for details.\n\n"
        
        for r in range(1, min(6, config.TOTAL_ROUNDS + 1)):
            round_picks = [p for p in order if p["round"] == r]
            round_text = ", ".join([f"{p['team_name']}" for p in round_picks])
            embed.add_field(name=f"Round {r}", value=round_text, inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mypicks", description="All pick numbers for a specific team")
    @app_commands.describe(team_name="Name or slot of the team")
    async def mypicks(self, interaction: discord.Interaction, team_name: str):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return
            
        order = self.generate_draft_order()
        
        # Fuzzy match or exact match team
        team_slot = None
        for i, t in enumerate(self.draft_config["teams"]):
            if team_name.lower() in t.lower() or team_name == str(i+1):
                team_slot = i + 1
                matched_name = t
                break
                
        if not team_slot:
            await interaction.response.send_message(f"Could not find team matching '{team_name}'.", ephemeral=True)
            return
            
        picks = []
        for i, pick in enumerate(order):
            if pick["team_slot"] == team_slot:
                picks.append(f"Round {pick['round']} (Overall #{i+1})")
                
        embed = discord.Embed(title=f"Draft Picks for {matched_name}", description="\n".join(picks), color=config.COLOUR_DRAFT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="currentpick", description="Who holds a given overall pick number")
    @app_commands.describe(pick="The overall pick number")
    async def currentpick(self, interaction: discord.Interaction, pick: int):
        if not self.in_allowed_channel(interaction):
            await interaction.response.send_message("You can't use this command here.", ephemeral=True)
            return

        order = self.generate_draft_order()
        
        if pick < 1 or pick > len(order):
            await interaction.response.send_message(f"Pick must be between 1 and {len(order)}.", ephemeral=True)
            return
            
        pick_data = order[pick - 1]
        
        embed = discord.Embed(title=f"Pick #{pick}", color=config.COLOUR_DRAFT)
        embed.description = f"**Team:** {pick_data['team_name']}\n**Round:** {pick_data['round']}\n**Pick in Round:** {((pick-1) % config.TOTAL_TEAMS) + 1}"
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setteam", description="Set a team name for a draft slot (Admin only)")
    @app_commands.describe(slot="Draft slot (1-8)", name="New team name")
    async def setteam(self, interaction: discord.Interaction, slot: int, name: str):
        if not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role to use this command.", ephemeral=True)
            return
            
        if slot < 1 or slot > config.TOTAL_TEAMS:
            await interaction.response.send_message(f"Slot must be between 1 and {config.TOTAL_TEAMS}.", ephemeral=True)
            return
            
        self.draft_config["teams"][slot - 1] = name
        await self.bot.db.save(config.DRAFT_CONFIG_FILE, self.draft_config)
        
        await interaction.response.send_message(f"✅ Slot {slot} is now **{name}**.")

async def setup(bot):
    await bot.add_cog(DraftDayDave(bot))
