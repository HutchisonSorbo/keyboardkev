import json
import os
import time
import discord
import logging

import config

log = logging.getLogger("CoachBot.Helpers")

class SimpleCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            data, expiry = self._cache[key]
            if time.time() < expiry:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, key, data, ttl_seconds):
        expiry = time.time() + ttl_seconds
        self._cache[key] = (data, expiry)

import io
import aiohttp
import asyncio

class DiscordDB:
    def __init__(self, bot):
        self.bot = bot
        self._cache = {}
        self._sync_lock = asyncio.Lock()
        self._history_synced = False
        self._attachment_map = {}

    async def _get_channel(self):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=config.MOD_LOG_CHANNEL)
            if channel:
                return channel
        return None

    async def load(self, filename: str) -> dict:
        """Loads JSON from the most recent attachment with the given filename in mod-log."""
        if filename in self._cache:
            return self._cache[filename]
            
        async with self._sync_lock:
            if not self._history_synced:
                channel = await self._get_channel()
                if channel:
                    try:
                        async for message in channel.history(limit=100):
                            if message.author == self.bot.user and message.attachments:
                                for attachment in message.attachments:
                                    fname = attachment.filename
                                    if fname not in self._attachment_map:
                                        self._attachment_map[fname] = attachment
                        self._history_synced = True
                    except Exception as e:
                        log.error(f"Error syncing DiscordDB history: {e}")

        basename = filename.split('/')[-1]
        if basename in self._attachment_map:
            try:
                json_bytes = await self._attachment_map[basename].read()
                data = json.loads(json_bytes.decode('utf-8'))
                self._cache[filename] = data
                return data
            except Exception as e:
                log.error(f"Error reading DiscordDB attachment for {filename}: {e}")
                
        self._cache[filename] = {}
        return {}

    async def save(self, filename: str, data: dict):
        """Saves JSON as an attachment in mod-log."""
        self._cache[filename] = data
        channel = await self._get_channel()
        if not channel:
            log.error(f"Cannot save {filename}, #{config.MOD_LOG_CHANNEL} not found.")
            return

        try:
            json_str = json.dumps(data, indent=4)
            file_obj = discord.File(fp=io.BytesIO(json_str.encode('utf-8')), filename=filename.split('/')[-1])
            await channel.send(f"💾 Render Database Sync: `{filename.split('/')[-1]}`", file=file_obj)
        except Exception as e:
            log.error(f"Error saving to DiscordDB for {filename}: {e}")

def format_embed(title, description, colour, footer=None):
    """Returns a standard discord.Embed object with consistent formatting."""
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def has_role(member, role_name):
    """Returns True if a member has a role matching role_name."""
    if not isinstance(member, discord.Member):
        return False
    return any(role.name.lower() == role_name.lower() for role in member.roles)
