import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.KeeperValue")

class KeeperValue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="keeper_value", description="Calculate the ultimate keeper value of a player")
    @app_commands.describe(
        player="Name of the player", 
        age="Current age (or age next season)", 
        average="Their fantasy average", 
        draft_cost="What round pick they cost to keep (1-23)"
    )
    async def keeper_value(self, interaction: discord.Interaction, player: str, age: int, average: float, draft_cost: int):
        if draft_cost < 1 or draft_cost > 30:
            await interaction.response.send_message("Mate, keep the draft cost between 1 and 30.", ephemeral=True)
            return
            
        if age < 18 or age > 45:
            await interaction.response.send_message("Age doesn't seem right. Unless Dustin Fletcher is playing again?", ephemeral=True)
            return

        # Keeper Score Formula:
        # Base: Their average
        # Age Factor: Premium on youth. (30 - age) * 1.5. So a 20yo gets +15, a 35yo gets -7.5
        # Cost Factor: Higher draft cost round = better value. Retaining at Rd 20 is better than Rd 1. (draft_cost) * 3
        
        age_factor = (30 - age) * 1.5
        cost_factor = draft_cost * 3
        
        score = average + age_factor + cost_factor
        score = round(score, 1)
        
        # Determine Kev's Verdict based on the score
        if score < 80:
            verdict = "🗑️ WAIVER TRASH"
            comment = "Throw 'em back in the pond. Not worth a spot on your roster. You're better off drafting a bloke who hasn't played since 1999."
            color = config.COLOUR_MOD # Red
        elif score < 100:
            verdict = "😬 BORDERLINE"
            comment = "Only keep 'em if you're absolutely desperate. Proper list clogger territory here."
            color = 0xFFA500 # Orange
        elif score < 120:
            verdict = "🍻 SOLID KEEPER"
            comment = "Yeah look, they'll do a job for ya. Worth holding onto, especially at that price."
            color = config.COLOUR_DRAFT # Gold
        elif score < 140:
            verdict = "🔥 LOCK HIM"
            comment = "Absolute no-brainer. Lock it in, shut the laptop, and enjoy the points."
            color = config.COLOUR_AFL # Orange/Red
        else:
            verdict = "👑 FRANCHISE SAVIOUR"
            comment = "I'd trade my dog for this bloke. Build your whole bloody dynasty around him."
            color = 0x9370DB # Purple

        embed = discord.Embed(title=f"📈 Keeper Value: {player}", color=color)
        
        embed.add_field(name="Stats", value=f"**Age:** {age}yo\n**Avg:** {average}\n**Cost:** Round {draft_cost}", inline=True)
        embed.add_field(name="Kev's Score", value=f"🏅 **{score}** pts", inline=True)
        
        embed.add_field(name=f"KEV RATING: {verdict}", value=f"*{comment}*", inline=False)
        
        embed.set_footer(text="Formula: Avg + (30-Age)*1.5 + (DraftCost)*3")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(KeeperValue(bot))
