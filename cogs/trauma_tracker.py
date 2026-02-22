import discord
from discord.ext import commands, tasks
import feedparser
import logging
from datetime import datetime
import asyncio
import re

import config
import helpers

log = logging.getLogger("CoachBot.TraumaTracker")

class TraumaTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen_articles = helpers.load_json(config.SEEN_ARTICLES_FILE)
        self.rss_check.start()

    def cog_unload(self):
        self.rss_check.cancel()

    @tasks.loop(minutes=config.POLL_INTERVAL_MINUTES)
    async def rss_check(self):
        try:
            async with self.bot.session.get(config.RSS_FEED_URL) as response:
                if response.status != 200:
                    log.error(f"RSS check failed: Status {response.status}")
                    return
                xml_data = await response.text()
            
            # feedparser blocks slightly, but it's very fast. So we can just call it
            feed = feedparser.parse(xml_data)
            
            new_articles = []
            
            for entry in feed.entries:
                link = entry.get('link')
                if not link or link in self.seen_articles:
                    continue
                
                new_articles.append(entry)
                self.seen_articles[link] = True # Mark seen immediately

            if new_articles:
                helpers.save_json(config.SEEN_ARTICLES_FILE, self.seen_articles)
                await self._post_articles(new_articles)
                
        except Exception as e:
            log.error(f"Error checking RSS feed: {e}")

    @rss_check.before_loop
    async def before_rss_check(self):
        await self.bot.wait_until_ready()

    async def _post_articles(self, articles):
        for guild in self.bot.guilds:
            news_channel = discord.utils.get(guild.text_channels, name=config.NEWS_CHANNEL)
            injury_channel = discord.utils.get(guild.text_channels, name=config.INJURY_CHANNEL)
            
            for entry in reversed(articles): # Oldest first to keep chronological order
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                raw_summary = entry.get('summary', 'No summary provided.')
                
                # Strip HTML tags
                summary = re.sub('<[^<]+?>', '', raw_summary).strip()
                
                # Check keywords to route
                content_to_check = f"{title} {summary}".lower()
                is_injury = any(kw.lower() in content_to_check for kw in config.INJURY_KEYWORDS)
                
                target_channel = injury_channel if is_injury else news_channel
                
                if not target_channel:
                    continue
                
                # Truncate summary if too long
                if len(summary) > 500:
                    summary = summary[:497] + "..."
                
                embed = helpers.format_embed(
                    title=title,
                    description=summary,
                    colour=config.COLOUR_AFL,
                    footer="Source: AFL.com.au News"
                )
                embed.url = link
                
                # Try to get published time
                if 'published' in entry:
                    embed.set_footer(text=f"AFL News • {entry.published}")
                
                try:
                    await target_channel.send(embed=embed)
                except discord.Forbidden:
                    log.error(f"Missing permissions to post news in {guild.name} #{target_channel.name}")

async def setup(bot):
    await bot.add_cog(TraumaTracker(bot))
