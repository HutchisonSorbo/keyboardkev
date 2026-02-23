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
        self.seen_articles = {}
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
                await self.bot.db.save(config.SEEN_ARTICLES_FILE, self.seen_articles)
                await self._post_articles(new_articles)
                
        except Exception as e:
            log.error(f"Error checking RSS feed: {e}")

    @rss_check.before_loop
    async def before_rss_check(self):
        await self.bot.wait_until_ready()
        
        # Load from DiscordDB first
        self.seen_articles = await self.bot.db.load(config.SEEN_ARTICLES_FILE)
        
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
                
                # Check keywords to route roughly
                content_to_check = f"{title} {summary}".lower()
                has_injury_keywords = any(kw.lower() in content_to_check for kw in config.INJURY_KEYWORDS)
                
                news_tldr = None
                injury_tldr = None
                
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
                                    
                                    # Prompt for News
                                    try:
                                        news_prompt = f'You are Keyboard Kev, a funny Australian pub-goer who loves AFL. Summarize the general AFL news from this article in 4-5 short, punchy bullet points starting with emojis to give coaches a quick TLDR. Focus specifically on the NEWS and details, NOT injuries. If there is absolutely NO general news (e.g. it is purely an injury update), reply ONLY with "NO_NEWS".\n\nArticle Title: {title}\nArticle Text: {article_text}'
                                        resp_news = await model.generate_content_async(news_prompt)
                                        if resp_news.text and "NO_NEWS" not in resp_news.text:
                                            news_tldr = resp_news.text
                                    except Exception as e:
                                        log.error(f"Failed to generate news TLDR: {e}")
                                        
                                    # Prompt for Injury (only if keywords matched to save API calls, or just always do it?)
                                    # We also check if news_tldr is None, in case it is purely an injury article we missed keywords for
                                    if has_injury_keywords or news_tldr is None:
                                        try:
                                            injury_prompt = f'You are Keyboard Kev, a funny Australian pub-goer who loves AFL. Summarize the AFL injury, medical and suspension updates from this article in 4-5 short, punchy bullet points starting with emojis to give coaches a quick TLDR. Focus specifically on INJURIES and availability. If there are NO injuries or suspensions mentioned, reply ONLY with "NO_INJURIES".\n\nArticle Title: {title}\nArticle Text: {article_text}'
                                            resp_injury = await model.generate_content_async(injury_prompt)
                                            if resp_injury.text and "NO_INJURIES" not in resp_injury.text:
                                                injury_tldr = resp_injury.text
                                        except Exception as e:
                                            log.error(f"Failed to generate injury TLDR: {e}")
                    except Exception as e:
                        log.error(f"Failed to fetch {link}: {e}")
                
                # Fallbacks if LLM fails or is disabled
                if not news_tldr and not injury_tldr:
                    # Legacy fallback logic
                    target_channel = injury_channel if has_injury_keywords else news_channel
                    if target_channel:
                        embed = helpers.format_embed(
                            title=title,
                            description=summary[:497] + "..." if len(summary) > 500 else summary,
                            colour=config.COLOUR_AFL,
                            footer="Source: AFL.com.au News"
                        )
                        embed.url = link
                        if 'published' in entry:
                            embed.set_footer(text=f"AFL News • {entry.published}")
                        try:
                            await target_channel.send(embed=embed)
                        except discord.Forbidden:
                            log.error(f"Missing permissions to post news in {guild.name}")
                    continue

                # Post News
                if news_tldr and news_channel:
                    embed = helpers.format_embed(
                        title=f"📰 {title}",
                        description=news_tldr,
                        colour=config.COLOUR_AFL,
                        footer="Source: AFL.com.au News"
                    )
                    embed.url = link
                    if 'published' in entry:
                        embed.set_footer(text=f"AFL News • {entry.published}")
                    try:
                        await news_channel.send(embed=embed)
                    except discord.Forbidden:
                        log.error(f"Missing permissions to post in {news_channel.name}")
                        
                # Post Injury
                if injury_tldr and injury_channel:
                    embed = helpers.format_embed(
                        title=f"🚑 {title}",
                        description=injury_tldr,
                        colour=config.COLOUR_MOD,
                        footer="Source: AFL.com.au Injuries"
                    )
                    embed.url = link
                    if 'published' in entry:
                        embed.set_footer(text=f"AFL Injuries • {entry.published}")
                    try:
                        await injury_channel.send(embed=embed)
                    except discord.Forbidden:
                        log.error(f"Missing permissions to post in {injury_channel.name}")

async def setup(bot):
    await bot.add_cog(TraumaTracker(bot))
