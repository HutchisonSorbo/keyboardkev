import discord
from discord import app_commands
from discord.ext import commands
import random
import logging

import config
import helpers

log = logging.getLogger("CoachBot.Fun")

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roast", description="Roast a league mate")
    @app_commands.describe(member="Who to roast")
    async def roast(self, interaction: discord.Interaction, member: discord.Member):
        if member == self.bot.user or member.bot:
            await interaction.response.send_message("Can't roast a bot, mate. Try roasting a human.")
            return
            
        roast = random.choice(config.ROASTS)
        msg = roast.format(target=member.mention)
        
        embed = discord.Embed(description=msg, color=config.COLOUR_FUN)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin to settle a debate")
    async def coinflip(self, interaction: discord.Interaction):
        is_heads = random.choice([True, False])
        if is_heads:
            msg = random.choice(config.COIN_HEADS_RESPONSES)
        else:
            msg = random.choice(config.COIN_TAILS_RESPONSES)
            
        embed = discord.Embed(description=msg, color=config.COLOUR_FUN)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the Magic 8-Ball a question")
    @app_commands.describe(question="Your yes/no question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        response = random.choice(config.EIGHT_BALL_RESPONSES)
        
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=config.COLOUR_FUN)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Roll a dice")
    @app_commands.describe(sides="Number of sides (default: 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("A dice needs at least 2 sides.", ephemeral=True)
            return
        if sides > 1000:
            await interaction.response.send_message("1000 sides is the maximum.", ephemeral=True)
            return
            
        result = random.randint(1, sides)
        embed = discord.Embed(description=f"🎲 Rolled a D{sides} and got: **{result}**", color=config.COLOUR_FUN)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
