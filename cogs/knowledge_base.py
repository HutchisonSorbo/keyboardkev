import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import logging
from datetime import datetime
import json
import pytz

import config

log = logging.getLogger("CoachBot.KnowledgeBase")

class KnowledgeBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        self.client_ready = False
        
        if not api_key:
            log.warning("GEMINI_API_KEY not found in .env. The /askkev command will not work.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # Create the model with System Instructions to enforce the persona
                # We do not use google_search_retrieval here as it is not strictly supported by discord bots yet without oauth,
                # but we will rely on the model itself knowing the instruction to "search" or use its latest knowledge.
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash", 
                    system_instruction=config.KEV_PERSONA_PROMPT,
                    tools='google_search_retrieval'
                )
                self.client_ready = True
                log.info("Gemini AI successfully initialized for /askkev")
            except Exception as e:
                log.error(f"Failed to initialize Gemini AI: {e}")

    def get_roster_context(self):
        try:
            with open("data/rosters.json", "r") as f:
                rosters = json.load(f)
                return f"\n\n[SYSTEM KNOWLEDGE (LEAGUE ROSTERS)]: {json.dumps(rosters)}"
        except (FileNotFoundError, json.JSONDecodeError):
            return "\n\n[SYSTEM KNOWLEDGE]: Rosters currently unavailable."

    @app_commands.command(name="askkev", description="Ask Kev a question about AFL history, players, or general footy")
    @app_commands.describe(question="What do you want to ask?", private="Hide the answer from the rest of the server?")
    async def ask_kev(self, interaction: discord.Interaction, question: str, private: bool = False):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        # Defer response since AI generation might take a couple of seconds
        await interaction.response.defer(ephemeral=private)
        
        try:
            # Inject current date for Warnie logic
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt_with_context = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser asked: {question}"

            # Generate the response
            response = self.model.generate_content(prompt_with_context)
            
            # Formatting the output nicely
            embed = discord.Embed(
                title="🍻 You asked Kev...",
                description=f"**\"{question}\"**\n\n{response.text}",
                color=config.COLOUR_FUN
            )
            embed.set_footer(text="Powered by 20 years of pub arguments (and Google Gemini)")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API: {e}")
            await interaction.followup.send("I've had too many frothies and my brain stopped working. Ask me again later.")

    @app_commands.command(name="kev_verdict", description="Get Kev's hot take on a trade or draft pick")
    @app_commands.describe(topic="The trade or pick you want Kev's opinion on")
    async def kev_verdict(self, interaction: discord.Interaction, topic: str):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            # Inject current date for Warnie logic
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt_with_context = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser is asking for your verdict on this trade or draft pick: {topic}\n\nPlease analyze this move and give a verdict using your persona."

            # Generate the response
            response = self.model.generate_content(prompt_with_context)
            
            # Formatting the output nicely
            embed = discord.Embed(
                title="🍺 Kev's Verdict",
                description=response.text[:4000],
                color=config.COLOUR_FUN
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
            
            await interaction.followup.send(content=f"**Topic:** {topic}", embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for verdict: {e}")
            await interaction.followup.send("Can't answer right now. Probably locked in a contract dispute.")

    @app_commands.command(name="trade_analyser", description="Get an analytical breakdown of a proposed trade")
    @app_commands.describe(team_a_gets="Players Team A receives", team_b_gets="Players Team B receives")
    async def trade_analyser(self, interaction: discord.Interaction, team_a_gets: str, team_b_gets: str):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser wants a deep analysis of a proposed trade.\nTeam A receives: {team_a_gets}\nTeam B receives: {team_b_gets}\n\nPlease provide a mathematical and strategic breakdown. Consider positional scarcity, keeper value, and recent form. Who wins the trade and why?"

            response = self.model.generate_content(prompt)
            
            embed = discord.Embed(
                title="⚖️ Trade Analyser",
                description=response.text[:4000],
                color=config.COLOUR_STATS
            )
            embed.add_field(name="Team A Gets", value=team_a_gets, inline=True)
            embed.add_field(name="Team B Gets", value=team_b_gets, inline=True)
            embed.set_footer(text="Trade Analyser | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for trade_analyser: {e}")
            await interaction.followup.send("My analyser is busted. I need another coffee.")

    @app_commands.command(name="matchup", description="Compare two players and pick who to start or Captain")
    @app_commands.describe(player1="First player", player2="Second player")
    async def matchup(self, interaction: discord.Interaction, player1: str, player2: str):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser wants a matchup comparison between these two players: {player1} vs {player2}.\n\nPlease compare their recent form, ceiling, and their upcoming match difficulty. Give a definitive answer on who the better start or Captain pick is this week."

            response = self.model.generate_content(prompt)
            
            embed = discord.Embed(
                title=f"🥊 Matchup: {player1} vs {player2}",
                description=response.text[:4000],
                color=config.COLOUR_FUN
            )
            embed.set_footer(text="Matchup Engine | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for matchup: {e}")
            await interaction.followup.send("Can't load the matchup right now.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and only listen to DMs if we are ready
        if message.author.bot or message.guild is not None or not self.client_ready:
            return
            
        # Give a typing indicator
        async with message.channel.typing():
            try:
                # Inject current date for Warnie logic
                tz = pytz.timezone(config.TIMEZONE)
                current_time = datetime.now(tz).strftime("%A, %d %B %Y %H:%M:%S")
                rosters = self.get_roster_context()
                prompt_with_context = f"[SYSTEM NOTIFICATION: Current date and time in Kilmore, Victoria is {current_time}. You are chatting privately in a Direct Message with {message.author.name}.]{rosters}\n\n{message.content}"
                
                response = self.model.generate_content(prompt_with_context)
                
                await message.reply(response.text)
                log.info(f"Replied privately to DM from {message.author.name}")
            except Exception as e:
                log.error(f"Error answering DM from {message.author.name}: {e}")
                await message.reply("Sorry mate, brain's foggy. Ask the Commish to check my logs.")

async def setup(bot):
    await bot.add_cog(KnowledgeBase(bot))
