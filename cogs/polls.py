import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

import config
import helpers

log = logging.getLogger("CoachBot.Polls")

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="The poll question",
        option1="Option 1", option2="Option 2",
        option3="Option 3 (optional)", option4="Option 4 (optional)",
        option5="Option 5 (optional)", option6="Option 6 (optional)",
        option7="Option 7 (optional)", option8="Option 8 (optional)"
    )
    async def create_poll(self, interaction: discord.Interaction, question: str, 
                         option1: str, option2: str, option3: str = None, 
                         option4: str = None, option5: str = None, 
                         option6: str = None, option7: str = None, option8: str = None):
        options = [o for o in [option1, option2, option3, option4, option5, option6, option7, option8] if o]
        
        if len(options) > config.MAX_POLL_OPTIONS:
            await interaction.response.send_message(f"Maximum {config.MAX_POLL_OPTIONS} options allowed.", ephemeral=True)
            return
            
        desc = ""
        for i, opt in enumerate(options):
            desc += f"{NUMBER_EMOJIS[i]} {opt}\n\n"
            
        embed = helpers.format_embed(title=f"📊 {question}", description=desc, colour=config.POLL_COLOUR)
        embed.set_author(name=f"Poll by {interaction.user.name}")
        
        if config.DEFAULT_POLL_DURATION_HOURS > 0:
            end_time = datetime.now() + timedelta(hours=config.DEFAULT_POLL_DURATION_HOURS)
            embed.set_footer(text=f"Poll ends • {end_time.strftime('%Y-%m-%d %H:%M')}")
            
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        
        for i in range(len(options)):
            await msg.add_reaction(NUMBER_EMOJIS[i])

    @app_commands.command(name="endpoll", description="End a poll and show results (Admin only)")
    @app_commands.describe(message_id="The message ID of the poll")
    async def end_poll(self, interaction: discord.Interaction, message_id: str):
        if not helpers.has_role(interaction.user, config.MOD_ROLE) and not helpers.has_role(interaction.user, config.DRAFT_ADMIN_ROLE):
            await interaction.response.send_message("You need the Commissioner role to end polls.", ephemeral=True)
            return
            
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.HTTPException, ValueError):
            await interaction.response.send_message("Poll message not found in this channel. Are you sure that's the right ID?", ephemeral=True)
            return
            
        if not msg.embeds or "Poll by" not in (msg.embeds[0].author.name or ""):
            await interaction.response.send_message("That doesn't look like a valid poll message.", ephemeral=True)
            return
            
        embed = msg.embeds[0]
        options_text = embed.description.split("\n\n")
        options = [o.strip()[2:].strip() for o in options_text if o.strip()]
        
        results = {}
        total_votes = 0
        
        for reaction in msg.reactions:
            if str(reaction.emoji) in NUMBER_EMOJIS:
                idx = NUMBER_EMOJIS.index(str(reaction.emoji))
                if idx < len(options):
                    # subtract 1 to remove the bot's own reaction
                    count = max(0, reaction.count - 1)
                    results[options[idx]] = count
                    total_votes += count
                    
        result_desc = ""
        for opt_text, count in results.items():
            pct = count / total_votes * 100 if total_votes > 0 else 0
            bars = int(pct / 10)
            bar_str = "█" * bars + "░" * (10 - bars)
            result_desc += f"**{opt_text}**\n{bar_str} {pct:.1f}% ({count} votes)\n\n"
            
        result_embed = helpers.format_embed(
            title=f"Results: {embed.title[2:] if embed.title.startswith('📊 ') else embed.title}",
            description=result_desc,
            colour=config.POLL_COLOUR,
            footer=f"Total votes: {total_votes}"
        )
        
        await interaction.response.send_message("Poll ended. Here are the results:", embed=result_embed)

async def setup(bot):
    await bot.add_cog(Polls(bot))
