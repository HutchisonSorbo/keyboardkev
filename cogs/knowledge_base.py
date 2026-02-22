import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import logging

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
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash", 
                    system_instruction=config.KEV_PERSONA_PROMPT
                )
                self.client_ready = True
                log.info("Gemini AI successfully initialized for /askkev")
            except Exception as e:
                log.error(f"Failed to initialize Gemini AI: {e}")

    @app_commands.command(name="askkev", description="Ask Kev a question about AFL history, players, or general footy")
    @app_commands.describe(question="What do you want to ask?")
    async def ask_kev(self, interaction: discord.Interaction, question: str):
        if not self.client_ready:
            await interaction.response.send_message("Sorry mate, the Commish hasn't given me my API brain yet.", ephemeral=True)
            return

        # Defer response since AI generation might take a couple of seconds
        await interaction.response.defer()
        
        try:
            # Generate the response
            response = self.model.generate_content(question)
            
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

async def setup(bot):
    await bot.add_cog(KnowledgeBase(bot))
