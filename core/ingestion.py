import feedparser
import asyncio

class NewsStreamer:
    def __init__(self):
        self.feeds = [
            "https://news.google.com/rss/search?q=polymarket+politics&hl=en-US",
            "https://www.coindesk.com/arc/outboundfeeds/rss/"
        ]
        self.seen = set()

    async def stream_data(self):
        while True:
            for url in self.feeds:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if entry.link not in self.seen:
                        self.seen.add(entry.link)
                        yield {
                            "title": entry.title,
                            "content": entry.summary,
                            "market_id": "AUTO_DETECTED_ID"
                        }
            await asyncio.sleep(10)