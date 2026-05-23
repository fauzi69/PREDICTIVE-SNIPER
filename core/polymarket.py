import httpx
from typing import Optional, Dict, List, Any
from core.cache import cache_manager
from core.config import Config
from core.logger import logger


class PolymarketClient:
    """Polymarket API client for market data and order execution."""

    def __init__(self):
        self.base_url = Config.POLYMARKET_API
        self.timeout = Config.REQUEST_TIMEOUT

    async def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch market data from Polymarket."""
        cache_key = f"market_{market_id}"
        cached = await cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Market cache hit: {market_id}")
            return cached

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/markets/{market_id}",
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                market_data = response.json()

                # Cache for 5 minutes
                await cache_manager.set(cache_key, market_data, ttl_seconds=300)
                return market_data
        except Exception as e:
            logger.error(f"Failed to fetch market {market_id}: {e}")
            return None

    async def search_markets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for markets by keyword."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/markets",
                    params={"search": query, "limit": limit},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Market search error: {e}")
            return []

    async def get_orderbook(self, market_id: str) -> Optional[Dict]:
        """Fetch current order book for a market."""
        cache_key = f"orderbook_{market_id}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/orderbook/{market_id}",
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                orderbook = response.json()

                # Cache for 1 minute (frequently changes)
                await cache_manager.set(cache_key, orderbook, ttl_seconds=60)
                return orderbook
        except Exception as e:
            logger.error(f"Orderbook fetch error: {e}")
            return None

    async def get_best_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """Get best bid/ask prices from order book."""
        orderbook = await self.get_orderbook(market_id)
        if not orderbook:
            return None

        try:
            yes_bids = orderbook.get("bids", {}).get("yes", [])
            yes_asks = orderbook.get("asks", {}).get("yes", [])

            best_bid = float(yes_bids[0][0]) if yes_bids else 0.0
            best_ask = float(yes_asks[0][0]) if yes_asks else 1.0

            return {
                "yes_bid": best_bid,
                "yes_ask": best_ask,
                "no_bid": 1 - best_ask,
                "no_ask": 1 - best_bid,
                "mid_price": (best_bid + best_ask) / 2,
            }
        except Exception as e:
            logger.error(f"Price extraction error: {e}")
            return None

    async def submit_order(
        self,
        market_id: str,
        side: str,
        amount: float,
        price: float,
        api_key: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Submit an order to Polymarket.
        Requires authentication (api_key).
        """
        if not api_key:
            logger.warning("No API key provided. Cannot submit order.")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/orders",
                    json={
                        "market_id": market_id,
                        "side": side.upper(),  # YES or NO
                        "amount": amount,
                        "price": price,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Order submission error: {e}")
            return None

    async def match_market_by_news(self, news_content: str) -> Optional[Dict]:
        """
        Try to automatically match news to a Polymarket market.
        Uses heuristics to find relevant market.
        """
        # Extract key entities/topics from news
        keywords = self._extract_keywords(news_content)
        if not keywords:
            return None

        # Search for markets
        for keyword in keywords:
            markets = await self.search_markets(keyword, limit=5)
            if markets:
                logger.info(f"Found {len(markets)} markets for '{keyword}'")
                # Return best match (sorted by volume)
                return sorted(
                    markets, key=lambda m: m.get("volume", 0), reverse=True
                )[0]

        return None

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract potential market keywords from text."""
        # Simple keyword extraction - can be enhanced with NLP
        stop_words = {
            "the",
            "a",
            "is",
            "and",
            "or",
            "to",
            "of",
            "in",
            "at",
            "by",
            "for",
        }

        words = text.lower().split()
        keywords = [
            w.strip(".,!?;:")
            for w in words
            if len(w) > 5 and w.lower() not in stop_words
        ]

        # Return top 5 unique keywords
        return list(set(keywords))[:5]