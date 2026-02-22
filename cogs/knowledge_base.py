import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import logging
from datetime import datetime
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
                    system_instruction=config.KEV_PERSONA_PROMPT
                )
                self.client_ready = True
                log.info("Gemini AI successfully initialized for /askkev")
            except Exception as e:
                log.error(f"Failed to initialize Gemini AI: {e}")

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
            prompt_with_context = f"[SYSTEM: Current date and time in Kilmore, Victoria is {current_time}]\n\nUser asked: {question}"

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
                prompt_with_context = f"[SYSTEM NOTIFICATION: Current date and time in Kilmore, Victoria is {current_time}. You are chatting privately in a Direct Message with {message.author.name}.]\n\n{message.content}"
                
                response = self.model.generate_content(prompt_with_context)
                
                await message.reply(response.text)
                log.info(f"Replied privately to DM from {message.author.name}")
            except Exception as e:
                log.error(f"Error answering DM from {message.author.name}: {e}")
                await message.reply("Sorry mate, brain's foggy. Ask the Commish to check my logs.")

async def setup(bot):
    await bot.add_cog(KnowledgeBase(bot))
