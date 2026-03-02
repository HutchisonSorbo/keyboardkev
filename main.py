import os
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import aiohttp
from threading import Thread
from flask import Flask

import config
import helpers

# Status rotation messages — {round} is replaced dynamically with the current AFL round
STATUS_MESSAGES = [
    "Lockout Thu ~7pm AEDT",
    "Waivers close Wed 11:59pm",
    "/askkev for advice",
    "/tips for tipping data",
    "AFL Round {round}",
    "8 coaches, 1 trophy",
    "Trust the data, not your gut",
    "/powerrankings for the pecking order",
]

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
        self.db = helpers.DiscordDB(self)

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
        if not self.rotate_status.is_running():
            self.rotate_status.start()

    @tasks.loop(minutes=5)
    async def rotate_status(self):
        """Rotate the bot's Discord status through contextual messages."""
        try:
            if not hasattr(self, '_status_index'):
                self._status_index = 0

            msg = STATUS_MESSAGES[self._status_index % len(STATUS_MESSAGES)]

            # Replace {round} with current AFL round if needed
            if '{round}' in msg:
                current_round = await self._get_current_round()
                msg = msg.replace('{round}', str(current_round) if current_round else '?')

            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=msg
                )
            )
            self._status_index += 1
        except Exception as e:
            log.error(f"Error rotating status: {e}")

    async def _get_current_round(self):
        """Fetch the current AFL round from Squiggle."""
        from datetime import datetime
        url = f"{config.SQUIGGLE_BASE_URL}?q=games;year={datetime.now().year}"
        headers = {"User-Agent": config.SQUIGGLE_USER_AGENT}
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for g in data.get('games', []):
                        if g.get('complete', 100) < 100:
                            return g.get('round')
                    games = data.get('games', [])
                    if games:
                        return games[-1].get('round')
        except Exception:
            pass
        return None

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

bot = CoachBot()

app = Flask('')

@app.route('/')
def home():
    return f"{config.BOT_NAME} is alive and analyzing stats!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

if __name__ == "__main__":
    try:
        # Start the Flask web server
        keep_alive()
        
        # discord.py handles the event loop properly with bot.run()
        bot.run(TOKEN, log_handler=None) # We set up our own logger above
    except KeyboardInterrupt:
        log.info("Shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        log.error(f"Fatal error: {e}")
