import feedparser
import asyncio
import httpx
from datetime import datetime
from typing import AsyncIterator, Dict, Any, Optional
from core.cache import cache_manager
from core.config import Config
from core.logger import logger

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None


class NewsStreamer:
    """Enhanced RSS feed streamer with deduplication and sentiment analysis."""

    def __init__(self):
        self.feeds = [
            "https://news.google.com/rss/search?q=polymarket+politics&hl=en-US",
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.cnbc.com/id/100003114/rss.html",
        ]
        self.request_timeout = Config.REQUEST_TIMEOUT
        self.update_interval = Config.RSS_UPDATE_INTERVAL
        self.max_cache = Config.MAX_NEWS_CACHE

    def _get_sentiment(self, text: str) -> Dict[str, float]:
        """Calculate sentiment score using TextBlob or simple heuristics."""
        if not text:
            return {"polarity": 0.0, "subjectivity": 0.5}

        if TextBlob:
            try:
                blob = TextBlob(text)
                return {
                    "polarity": max(-1.0, min(1.0, blob.sentiment.polarity)),
                    "subjectivity": blob.sentiment.subjectivity,
                }
            except Exception as e:
                logger.debug(f"Sentiment analysis error: {e}")

        # Fallback: simple keyword-based sentiment
        positive_keywords = [
            "rise",
            "surge",
            "gain",
            "bull",
            "outperform",
            "win",
            "breakthrough",
        ]
        negative_keywords = [
            "fall",
            "crash",
            "loss",
            "bear",
            "underperform",
            "fail",
            "collapse",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        polarity = (positive_count - negative_count) / max(1, positive_count + negative_count)
        return {"polarity": max(-1.0, min(1.0, polarity)), "subjectivity": 0.5}

    async def _fetch_feed(self, url: str) -> list:
        """Fetch a single RSS feed with error handling."""
        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return feedparser.parse(response.text).entries
        except Exception as e:
            logger.warning(f"Feed fetch error ({url}): {e}")
            return []

    def _is_relevant(self, title: str, summary: str = "") -> bool:
        """Filter relevant news based on keywords."""
        relevant_keywords = [
            "polymarket",
            "prediction market",
            "crypto",
            "blockchain",
            "bitcoin",
            "ethereum",
            "fed",
            "inflation",
            "election",
            "politics",
            "economy",
            "market",
            "surge",
            "crash",
        ]

        content = (title + " " + summary).lower()
        return any(keyword in content for keyword in relevant_keywords)

    async def stream_data(self) -> AsyncIterator[Dict[str, Any]]:
        """Stream news from all feeds with continuous polling."""
        seen_hashes = set()

        while True:
            try:
                for url in self.feeds:
                    entries = await self._fetch_feed(url)

                    for entry in entries:
                        # Extract data
                        title = getattr(entry, "title", "")
                        summary = getattr(entry, "summary", "")
                        link = getattr(entry, "link", "")
                        published = getattr(entry, "published", "")

                        if not title or not link:
                            continue

                        # Check relevance
                        if not self._is_relevant(title, summary):
                            continue

                        # Deduplicate
                        content_hash = cache_manager.hash_key(link)
                        if content_hash in seen_hashes:
                            continue

                        # Check cache
                        if await cache_manager.exists(content_hash):
                            logger.debug(f"News already processed: {title[:50]}...")
                            seen_hashes.add(content_hash)
                            continue

                        seen_hashes.add(content_hash)

                        # Analyze sentiment
                        sentiment = self._get_sentiment(title + " " + summary)

                        # Cache and yield
                        news_item = {
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "published": published,
                            "source": url.split("/")[2],
                            "sentiment": sentiment,
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                        await cache_manager.set(content_hash, news_item, ttl_seconds=86400)
                        logger.info(
                            f"📰 New news: {title[:60]}... (Sentiment: {sentiment['polarity']:.2f})"
                        )
                        yield news_item

                # Sleep before next poll
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Stream error: {e}")
                await asyncio.sleep(self.update_interval)