import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.FuturePicks")

class FuturePicks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # data structure: {user_id: {"team_name": str, "picks": [{"year": int, "round": int, "original_owner": str}]}}
        self.picks_data = {}
        
    async def cog_load(self):
        self.bot.loop.create_task(self.initialize_data())
        
    async def initialize_data(self):
        await self.bot.wait_until_ready()
        self.picks_data = await self.bot.db.load("future_picks.json")
        
    @app_commands.command(name="picks", description="View draft pick capital for a coach")
    @app_commands.describe(member="Optional: View a specific coach's picks")
    async def view_picks(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        target_id = str(target.id)
        
        # If they don't have entry, generate their default picks
        if target_id not in self.picks_data:
            await self._initialize_default_picks(target)
            
        data = self.picks_data[target_id]
        
        embed = discord.Embed(title=f"📋 {target.display_name}'s Draft Capital", color=config.COLOUR_DRAFT)
        
        # Group by year
        picks_by_year = {}
        for p in data["picks"]:
            year = p["year"]
            if year not in picks_by_year:
                picks_by_year[year] = []
            picks_by_year[year].append(p)
            
        for year in sorted(picks_by_year.keys()):
            desc = ""
            sorted_picks = sorted(picks_by_year[year], key=lambda x: x["round"])
            for p in sorted_picks:
                orig = p.get("original_owner")
                owner_str = f" (*via {orig}*)" if orig and orig != target.display_name else ""
                desc += f"• Round {p['round']}{owner_str}\n"
                
            embed.add_field(name=f"Season {year}", value=desc, inline=False)
            
        embed.set_footer(text="These are keeper league future picks. Admin runs /tradepick to move them.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tradepick", description="Transfer a future draft pick between coaches (Admin)")
    @app_commands.describe(
        from_coach="Coach trading the pick away", 
        to_coach="Coach receiving the pick",
        year="Draft year (e.g. 2027)",
        round_num="Round number of the pick (e.g. 1)"
    )
    async def trade_pick(self, interaction: discord.Interaction, from_coach: discord.Member, to_coach: discord.Member, year: int, round_num: int):
        if not helpers.has_role(interaction.user, config.MOD_ROLE) and not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need Commissioner permissions to log pick trades.", ephemeral=True)
            return

        from_id = str(from_coach.id)
        to_id = str(to_coach.id)
        
        if from_id not in self.picks_data: await self._initialize_default_picks(from_coach)
        if to_id not in self.picks_data: await self._initialize_default_picks(to_coach)
            
        from_picks = self.picks_data[from_id]["picks"]
        
        # Find the specific pick
        pick_to_move = None
        for p in from_picks:
            if p["year"] == year and p["round"] == round_num:
                # We'll grab the first one we find that matches
                pick_to_move = p
                break
                
        if not pick_to_move:
             await interaction.response.send_message(f"Error: {from_coach.display_name} does not own a {year} Round {round_num} pick to trade.", ephemeral=True)
             return
             
        # Move it
        from_picks.remove(pick_to_move)
        
        # We need to make sure the original owner tracking is kept if it's already someone else's,
        # otherwise, if it's from_coach's original pick, we set original_owner to them
        if "original_owner" not in pick_to_move or not pick_to_move["original_owner"]:
             pick_to_move["original_owner"] = from_coach.display_name
             
        self.picks_data[to_id]["picks"].append(pick_to_move)
        
        await self.bot.db.save("future_picks.json", self.picks_data)
        
        embed = discord.Embed(
            title="🤝 Pick Trade Executed",
            description=f"**{from_coach.mention}** has traded their {year} **Round {round_num}** pick to **{to_coach.mention}**.",
            color=config.COLOUR_DRAFT
        )
        await interaction.response.send_message(embed=embed)
        
    async def _initialize_default_picks(self, member):
        # By default give them their own picks for the next 2 years for 5 rounds
        current_year = datetime.now().year
        picks = []
        for y in [current_year, current_year + 1]:
            for r in range(1, 6): # Default 5 rounds for a keeper rookie/FA draft
                picks.append({"year": y, "round": r, "original_owner": member.display_name})
                
        self.picks_data[str(member.id)] = {
            "team_name": member.display_name,
            "picks": picks
        }
        await self.bot.db.save("future_picks.json", self.picks_data)

async def setup(bot):
    await bot.add_cog(FuturePicks(bot))
