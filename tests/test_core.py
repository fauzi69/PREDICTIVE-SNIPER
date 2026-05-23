import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from core.config import Config
from core.ingestion import NewsStreamer
from core.brain import ProbabilityRouter
from core.evaluator import OpportunityFinder
from core.cache import cache_manager


class TestConfig:
    """Test configuration management."""

    def test_config_defaults(self):
        """Test that default config values are set."""
        assert Config.MIN_MARGIN > 0
        assert Config.MAX_TRADE_SIZE > 0
        assert Config.DRY_RUN in [True, False]

    def test_config_validation(self):
        """Test configuration validation."""
        with patch.dict("os.environ", {"MIMO_API_KEY": "test"}):
            Config.MIMO_API_KEY = "test"
            assert Config.validate()


class TestNewsStreamer:
    """Test news ingestion module."""

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        """Test sentiment scoring."""
        streamer = NewsStreamer()

        # Positive sentiment
        pos_sentiment = streamer._get_sentiment(
            "Bitcoin surges to new highs!"
        )
        assert pos_sentiment["polarity"] > 0

        # Negative sentiment
        neg_sentiment = streamer._get_sentiment(
            "Market crash reported"
        )
        assert neg_sentiment["polarity"] < 0

        # Neutral
        neutral = streamer._get_sentiment("The weather is 50 degrees")
        assert neutral["polarity"] == 0

    def test_relevance_filter(self):
        """Test news relevance filtering."""
        streamer = NewsStreamer()

        # Relevant news
        assert streamer._is_relevant(
            "Bitcoin surges 20%",
            "Crypto market gains"
        )

        # Irrelevant news
        assert not streamer._is_relevant(
            "Celebrity gossip",
            "Movie star news"
        )


class TestProbabilityRouter:
    """Test AI probability estimation."""

    def test_parse_probability(self):
        """Test probability parsing from LLM responses."""
        router = ProbabilityRouter()

        # Test various formats
        assert router._parse_probability("0.75") == 0.75
        assert router._parse_probability("75") == 0.75
        assert router._parse_probability("The probability is 0.85") == 0.85
        assert 0 <= router._parse_probability("hello") <= 1  # Fallback
        assert router._parse_probability("invalid") is None


class TestOpportunityFinder:
    """Test market opportunity evaluation."""

    def test_should_bet_with_edge(self):
        """Test betting decision with clear edge."""
        evaluator = OpportunityFinder(min_margin=0.20)

        # Clear edge (AI: 70%, Market: 40%)
        should_bet, analysis = evaluator.should_bet(0.70, 0.40)
        assert should_bet is True
        assert analysis["margin"] == 0.30

        # No edge (AI: 45%, Market: 40%)
        should_bet, analysis = evaluator.should_bet(0.45, 0.40)
        assert should_bet is False

    def test_kelly_criterion(self):
        """Test Kelly Criterion bet sizing."""
        evaluator = OpportunityFinder()

        # Even odds with 60% win probability
        kelly = evaluator._kelly_criterion(0.60, 0.50)
        assert 0 < kelly <= 0.25

        # Invalid probabilities
        assert evaluator._kelly_criterion(0, 0.5) == 0
        assert evaluator._kelly_criterion(1, 0.5) == 0

    def test_bet_amount_calculation(self):
        """Test bet amount calculation."""
        evaluator = OpportunityFinder(min_margin=0.20)

        analysis = {
            "kelly_fraction": 0.10,
            "margin": 0.25,
            "expected_value": 0.5,
        }

        balance = 1000
        bet_amount = evaluator.calculate_bet_amount(analysis, balance)
        assert bet_amount == 100  # 10% of 1000

        # Respect max trade size
        balance = 100000
        bet_amount = evaluator.calculate_bet_amount(analysis, balance)
        assert bet_amount <= Config.MAX_TRADE_SIZE

    def test_trade_history(self):
        """Test trade recording and statistics."""
        evaluator = OpportunityFinder()

        evaluator.record_trade("market_1", 0.70, 0.40, 100, "YES")
        evaluator.record_trade("market_2", 0.60, 0.50, 200, "NO")

        stats = evaluator.get_performance_stats()
        assert stats["total_trades"] == 2
        assert stats["total_volume_usdc"] == 300
        assert stats["avg_trade_size"] == 150


class TestCache:
    """Test caching mechanisms."""

    @pytest.mark.asyncio
    async def test_sqlite_cache(self):
        """Test SQLite cache backend."""
        cache = cache_manager

        # Set and get
        await cache.set("test_key", {"value": 123}, ttl_seconds=3600)
        result = await cache.get("test_key")
        assert result == {"value": 123}

        # Exists
        assert await cache.exists("test_key")

        # Delete
        await cache.delete("test_key")
        assert not await cache.exists("test_key")

    @pytest.mark.asyncio
    async def test_hash_key(self):
        """Test key hashing."""
        cache = cache_manager

        hash1 = cache.hash_key("same_content")
        hash2 = cache.hash_key("same_content")
        assert hash1 == hash2

        hash3 = cache.hash_key("different_content")
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
