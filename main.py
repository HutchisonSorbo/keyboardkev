import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("CoachBot")

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    log.error("DISCORD_TOKEN not found in .env file. Exiting.")
    exit(1)

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True

class CoachBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None # Disabling default help command to use our custom one
        )
        self.session = None

    async def setup_hook(self):
        # Create a shared aiohttp session
        self.session = aiohttp.ClientSession()

        # Load all cogs from the cogs directory
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        loaded_count = 0
        
        # Make sure cogs dir exists
        os.makedirs(cogs_dir, exist_ok=True)
        
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    log.info(f"Loaded extension: {cog_name}")
                    loaded_count += 1
                except Exception as e:
                    log.error(f"Failed to load extension {cog_name}: {e}")

        log.info(f"Loaded {loaded_count} cogs.")

        # Sync slash commands globally
        try:
            synced = await self.tree.sync()
            log.info(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            log.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        log.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        log.info(f"Currently in {len(self.guilds)} server(s).")
        log.info(f"{config.BOT_NAME} is fully online and ready.")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

bot = CoachBot()

if __name__ == "__main__":
    try:
        # discord.py handles the event loop properly with bot.run()
        bot.run(TOKEN, log_handler=None) # We set up our own logger above
    except KeyboardInterrupt:
        log.info("Shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        log.error(f"Fatal error: {e}")
