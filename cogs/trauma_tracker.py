import discord
from discord.ext import commands, tasks
import feedparser
import logging
from datetime import datetime
import asyncio
import re
import os
from bs4 import BeautifulSoup
import google.generativeai as genai

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
            # AFL.com.au uses Cloudflare, which blocks default python user agents. We must provide one.
            headers = {
                "User-Agent": "KeyboardCoachesDiscordBot/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            }
            async with self.bot.session.get(config.RSS_FEED_URL, headers=headers) as response:
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
        
        # Populate seen_articles from channel history to survive Render ephemeral storage restarts
        for guild in self.bot.guilds:
            for channel_name in [config.NEWS_CHANNEL, config.INJURY_CHANNEL]:
                channel = discord.utils.get(guild.text_channels, name=channel_name)
                if channel:
                    try:
                        async for message in channel.history(limit=50):
                            if message.embeds and message.author == self.bot.user:
                                url = message.embeds[0].url
                                if url:
                                    self.seen_articles[url] = True
                    except Exception as e:
                        log.error(f"Error reading history for {channel_name}: {e}")

    async def _post_articles(self, articles):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            
        for guild in self.bot.guilds:
            news_channel = discord.utils.get(guild.text_channels, name=config.NEWS_CHANNEL)
            injury_channel = discord.utils.get(guild.text_channels, name=config.INJURY_CHANNEL)
            
            for entry in reversed(articles): # Oldest first to keep chronological order
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                raw_summary = entry.get('summary', 'No summary provided.')
                
                # Strip HTML tags for the fallback summary
                summary = re.sub('<[^<]+?>', '', raw_summary).strip()
                
                # Check keywords to route
                content_to_check = f"{title} {summary}".lower()
                is_injury = any(kw.lower() in content_to_check for kw in config.INJURY_KEYWORDS)
                
                target_channel = injury_channel if is_injury else news_channel
                
                if not target_channel:
                    continue
                
                # Attempt to get a bigger TLDR using Gemini
                tldr = None
                if api_key:
                    try:
                        async with self.bot.session.get(link) as resp:
                            if resp.status == 200:
                                html = await resp.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                paragraphs = soup.find_all('p')
                                article_text = " ".join([p.get_text() for p in paragraphs[:10]])
                                
                                if len(article_text) > 200:
                                    model = genai.GenerativeModel("gemini-2.5-flash")
                                    prompt = f'You are Keyboard Kev, a funny Australian pub-goer who loves AFL. Summarize this AFL article in 3 short, punchy bullet points to give coaches a quick TLDR. Do not use generic pleasantries, just give the 3 bullet points starting with emojis.\n\nArticle Title: {title}\nArticle Text: {article_text}'
                                    response = await model.generate_content_async(prompt)
                                    if response.text:
                                        tldr = response.text
                    except Exception as e:
                        log.error(f"Failed to generate custom TLDR for {link}: {e}")
                
                if tldr:
                    summary = tldr
                elif len(summary) > 500:
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
