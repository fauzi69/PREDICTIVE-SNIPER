"""
News Ingestion Module
=====================
Real-time RSS feed streaming with deduplication and error resilience.
"""

import feedparser
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List

logger = logging.getLogger(__name__)


class NewsStreamer:
    """
    Asynchronous news streamer that continuously monitors multiple RSS feeds
    for prediction market-relevant content.
    
    Features:
        - Multi-feed aggregation
        - Automatic deduplication via link tracking
        - Configurable polling interval
        - Graceful error handling per feed
    """

    DEFAULT_FEEDS: List[str] = [
        "https://news.google.com/rss/search?q=polymarket+politics&hl=en-US",
        "https://news.google.com/rss/search?q=prediction+market+crypto&hl=en-US",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]

    def __init__(self, feeds: List[str] | None = None, poll_interval: int = 10):
        """
        Initialize the NewsStreamer.
        
        Args:
            feeds: List of RSS feed URLs to monitor. Uses defaults if None.
            poll_interval: Seconds between polling cycles.
        """
        self.feeds = feeds or self.DEFAULT_FEEDS
        self.poll_interval = poll_interval
        self.seen: set = set()
        self._running: bool = False

    async def stream_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Continuously stream new articles from configured RSS feeds.
        
        Yields:
            Dict containing 'title', 'content', 'link', and 'source' keys.
        """
        self._running = True
        logger.info(f"[INGESTION] Starting stream with {len(self.feeds)} feeds...")

        while self._running:
            for url in self.feeds:
                try:
                    feed = feedparser.parse(url)

                    if feed.bozo:
                        logger.warning(f"[INGESTION] Feed parse warning: {url}")

                    for entry in feed.entries:
                        link = getattr(entry, "link", None)
                        if link and link not in self.seen:
                            self.seen.add(link)
                            yield {
                                "title": getattr(entry, "title", "Unknown"),
                                "content": getattr(entry, "summary", ""),
                                "link": link,
                                "source": url.split("/")[2],
                            }
                except Exception as e:
                    logger.error(f"[INGESTION] Error parsing feed {url}: {e}")
                    continue

            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        """Signal the streamer to stop after current cycle."""
        self._running = False
        logger.info("[INGESTION] Stream stopped.")
