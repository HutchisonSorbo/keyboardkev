import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import types
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
                self.client = genai.Client(api_key=api_key)
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

    async def _generate(self, prompt: str) -> str:
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=config.WARNIE_PERSONA_PROMPT,
            )
        )
        return response.text

    @app_commands.command(name="askkev", description="Ask Kev a question about AFL history, players, or general footy")
    @app_commands.describe(question="What do you want to ask?", private="Hide the answer from the rest of the server? (Default: Yes)")
    async def ask_kev(self, interaction: discord.Interaction, question: str, private: bool = True):
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
            response_text = await self._generate(prompt_with_context)
            
            # Formatting the output nicely
            embed = discord.Embed(
                title="🍻 You asked Kev...",
                description=f"**\"{question}\"**\n\n{response_text}",
                color=config.COLOUR_FUN
            )
            embed.set_footer(text="Powered by 20 years of AFL Fantasy expertise (and Google Gemini)")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API: {e}")
            await interaction.followup.send("Sorry mate, I can't look at that right now. Try again later.")

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
            response_text = await self._generate(prompt_with_context)
            
            # Formatting the output nicely
            embed = discord.Embed(
                title="🍺 Kev's Verdict",
                description=response_text[:4000],
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

            response_text = await self._generate(prompt)
            
            embed = discord.Embed(
                title="⚖️ Trade Analyser",
                description=response_text[:4000],
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

            response_text = await self._generate(prompt)
            
            embed = discord.Embed(
                title=f"🥊 Matchup: {player1} vs {player2}",
                description=response_text[:4000],
                color=config.COLOUR_FUN
            )
            embed.set_footer(text="Matchup Engine | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for matchup: {e}")
            await interaction.followup.send("Can't load the matchup right now.")

    @app_commands.command(name="captains", description="Get Warnie's top Captain and Vice Captain picks for the round")
    async def captains(self, interaction: discord.Interaction):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser wants your top Captain and Vice Captain recommendations for the upcoming AFL round.\n\nPlease provide a detailed breakdown of 1-2 Vice Captain options (early games for loop-holing) and 1-2 Captain options. Consider match difficulty, historical scoring against the opponent, and recent form."

            response_text = await self._generate(prompt)
            
            embed = discord.Embed(
                title="©️ Warnie's Captains",
                description=response_text[:4000],
                color=config.COLOUR_AFL
            )
            embed.set_footer(text="Captains Engine | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for captains: {e}")
            await interaction.followup.send("My crystal ball for captains is broken right now. Check back later.")

    @app_commands.command(name="fixture", description="Ask Warnie about the upcoming fixture difficulty (Calvin's Scale of Hardness)")
    @app_commands.describe(team_or_player="The team or player you want fixture analysis on")
    async def fixture(self, interaction: discord.Interaction, team_or_player: str):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser wants a fixture analysis on: {team_or_player}.\n\nPlease analyze the upcoming 3-4 matches for this player or team using the logic of Calvin's Scale of Hardness. Are they soft or hard matchups? Does it make them a buy, hold, or sell?"

            response_text = await self._generate(prompt)
            
            embed = discord.Embed(
                title=f"📅 Fixture Analysis: {team_or_player}",
                description=response_text[:4000],
                color=config.COLOUR_STATS
            )
            embed.set_footer(text="Scale of Hardness | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for fixture: {e}")
            await interaction.followup.send("Scale of Hardness is offline. Give it a minute.")

    @app_commands.command(name="rookies", description="Get Warnie's top rookie targets and cash cows for the week")
    async def rookies(self, interaction: discord.Interaction):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            tz = pytz.timezone(config.TIMEZONE)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            rosters = self.get_roster_context()
            prompt = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]{rosters}\n\nUser wants a breakdown of the best rookie targets / cash cows to trade in this week.\n\nPlease provide 2-3 basement priced players that are locked into best 22 roles with good job security, high time on ground, or friendly roles."

            response_text = await self._generate(prompt)
            
            embed = discord.Embed(
                title="🐄 Rookie Watchlist",
                description=response_text[:4000],
                color=config.COLOUR_FUN
            )
            embed.set_footer(text="Rookie Scanner | Keyboard Kev")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log.error(f"Error calling Gemini API for rookies: {e}")
            await interaction.followup.send("Cows haven't been milked yet. Too early to tell.")

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
                
                response_text = await self._generate(prompt_with_context)
                
                await message.reply(response_text)
                log.info(f"Replied privately to DM from {message.author.name}")
            except Exception as e:
                log.error(f"Error answering DM from {message.author.name}: {e}")
                await message.reply("Sorry mate, brain's foggy. Ask the Commish to check my logs.")

async def setup(bot):
    await bot.add_cog(KnowledgeBase(bot))
