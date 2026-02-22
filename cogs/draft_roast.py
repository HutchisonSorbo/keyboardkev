import discord
from discord import app_commands
from discord.ext import commands
import random
import logging

import config
import helpers

log = logging.getLogger("CoachBot.DraftRoast")

class DraftRoast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="draftpick", description="Announce a draft pick and let Kev roast it (Admin)")
    @app_commands.describe(team="The team making the pick", player="The drafted player")
    async def draft_pick(self, interaction: discord.Interaction, team: str, player: str):
        if not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("Only the Commish can officially announce draft picks.", ephemeral=True)
            return

        roast = random.choice(config.DRAFT_ROASTS)
        msg = roast.format(team=team, player=player)
        
        embed = discord.Embed(
            title=f"🚨 THE PICK IS IN 🚨",
            description=f"**{team}** selects...\n\n### {player} 🏉\n\n*Kev says:* \"{msg}\"",
            color=config.COLOUR_DRAFT
        )
        embed.set_thumbnail(url="https://keeperfantasy.com/wp-content/uploads/2021/11/The-Keeper-App-Logo-2.png") # Give a shoutout to the Keeper App
        
        # Post to the channel
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DraftRoast(bot))
