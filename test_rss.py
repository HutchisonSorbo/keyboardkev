import asyncio
import aiohttp
import feedparser

async def test_rss():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*"
    }
    url = "https://www.afl.com.au/rss"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            feed = feedparser.parse(text)
            print(f"Entries: {len(feed.entries)}")
            if len(feed.entries) > 0:
                print(feed.entries[0].title)

if __name__ == "__main__":
    asyncio.run(test_rss())
