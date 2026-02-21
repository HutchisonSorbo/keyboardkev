import json
import os
import time
import discord

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

def load_json(filepath):
    """Loads a JSON file, returns empty dict if file does not exist yet. Creates the file if missing."""
    if not os.path.exists(filepath):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        save_json(filepath, {})
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filepath, data):
    """Saves data to a JSON file with indentation."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

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
