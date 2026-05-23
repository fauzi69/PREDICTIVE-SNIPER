# MIMO Predictive Sniper - API Documentation

## Overview

This document describes the modules and APIs available in the MIMO Predictive Sniper system.

## Core Modules

### Config Module

Configuration management with validation and logging.

**Location**: `core/config.py`

**Key Properties**:
```python
Config.PRIVATE_KEY          # Polygon wallet private key
Config.POLYGON_RPC          # Polygon RPC endpoint
Config.MIMO_API_KEY         # MIMO platform API key
Config.MIN_MARGIN          # Minimum edge threshold (default: 0.20 = 20%)
Config.MAX_TRADE_SIZE      # Max trade size in USDC (default: 1000)
Config.CACHE_BACKEND       # Cache type: 'sqlite' or 'redis'
Config.DRY_RUN             # Disable real transactions if true
Config.LOG_LEVEL           # Logging level: DEBUG, INFO, WARNING, ERROR
```

**Methods**:
```python
Config.validate()          # Validate critical config values
Config.log_summary()       # Log config summary on startup
```

---

### Logger Module

Comprehensive logging with file and console output.

**Location**: `core/logger.py`

**Example**:
```python
from core.logger import logger

logger.info("Application started")
logger.warning("Rate limit approaching")
logger.error("Transaction failed", exc_info=True)
logger.debug("Detailed debugging info")
```

**Log Format**:
```
2024-05-23 15:30:45 - core.brain - INFO - ✅ MIMO probability: 0.75
```

---

### Cache Module

Smart caching with SQLite and Redis backends.

**Location**: `core/cache.py`

**Interface**:
```python
from core.cache import cache_manager

# Set value with TTL
await cache_manager.set(key, value, ttl_seconds=3600)

# Get value
value = await cache_manager.get(key)

# Check existence
exists = await cache_manager.exists(key)

# Delete key
await cache_manager.delete(key)

# Hash content for keys
hash_key = cache_manager.hash_key(content)
```

**Backends**:
- **SQLite** (default): Local file-based caching
- **Redis**: Distributed caching for multi-instance setups

---

### Ingestion Module

Real-time news streaming with sentiment analysis.

**Location**: `core/ingestion.py`

**NewsStreamer Class**:
```python
from core.ingestion import NewsStreamer

streamer = NewsStreamer()

# Stream news items
async for news in streamer.stream_data():
    print(news['title'])
    print(news['sentiment'])  # {'polarity': -0.5, 'subjectivity': 0.6}
```

**News Item Structure**:
```python
{
    "title": str,           # News headline
    "summary": str,         # Article summary/content
    "link": str,            # Source URL
    "published": str,       # Publication timestamp
    "source": str,          # Feed domain
    "sentiment": {
        "polarity": float,   # -1.0 (negative) to 1.0 (positive)
        "subjectivity": float  # 0.0 (objective) to 1.0 (subjective)
    },
    "timestamp": str        # When fetched (ISO 8601)
}
```

---

### Brain Module

AI-powered probability estimation with automatic fallback.

**Location**: `core/brain.py`

**ProbabilityRouter Class**:
```python
from core.brain import ProbabilityRouter

brain = ProbabilityRouter()

# Get single probability estimate
probability, source = await brain.get_probability(content)
# Returns: (float, "MIMO" | "GROQ" | "NEUTRAL")

# Get consensus from multiple AIs
consensus = await brain.get_multiple_opinions(content)
# Returns: float (averaged probability)
```

**Features**:
- Primary: Xiaomi MIMO AI
- Fallback 1: Groq (free tier)
- Fallback 2: Neutral (0.5)
- Built-in response caching
- Automatic timeout handling

---

### Evaluator Module

Market opportunity analysis and bet sizing.

**Location**: `core/evaluator.py`

**OpportunityFinder Class**:
```python
from core.evaluator import OpportunityFinder

evaluator = OpportunityFinder(min_margin=0.20)

# Check if trading opportunity exists
should_bet, analysis = evaluator.should_bet(ai_prob=0.70, market_price=0.40)

# analysis contains:
# {
#     "ai_probability": 0.70,
#     "market_price": 0.40,
#     "margin": 0.30,              # Absolute difference
#     "edge_percentage": 75.0,      # Relative advantage
#     "expected_value": 0.75,       # EV of the bet
#     "kelly_fraction": 0.15        # Optimal bet size (15%)
# }

# Calculate optimal bet amount
bet_amount = evaluator.calculate_bet_amount(analysis, balance=1000)
# Capped at MAX_TRADE_SIZE

# Record trade for tracking
evaluator.record_trade(
    market_id="market_123",
    ai_prob=0.70,
    market_price=0.40,
    amount=150.0,
    side="YES"
)

# Get performance statistics
stats = evaluator.get_performance_stats()
# {
#     "total_trades": 5,
#     "total_volume_usdc": 750.0,
#     "avg_trade_size": 150.0,
#     "trades": [...]
# }
```

**Bet Sizing**:
Uses Kelly Criterion for optimal position sizing:
```
Kelly% = (bp - q) / b
where b = odds, p = win probability, q = 1 - p
```
Capped at 25% to prevent over-leverage.

---

### Execution Module

Web3 transaction signing and execution on Polygon.

**Location**: `core/execution.py`

**Web3Signer Class**:
```python
from core.execution import Web3Signer

executor = Web3Signer()

# Check USDC balance
balance = executor.get_balance()  # Returns: float (USDC)

# Place order
success, tx_hash = await executor.place_order(
    market_id="market_123",
    amount_usdc=100.0,
    side="YES",
    polymarket_address="0x..."  # Optional
)

# Estimate gas costs
gas_info = executor.estimate_gas_cost(amount_usdc=100.0)
# {
#     "gas_price_gwei": 40.5,
#     "gas_limit": 100000,
#     "total_cost_matic": 0.004
# }
```

**Features**:
- USDC token interaction
- Automatic gas estimation
- Transaction signing with private key
- Receipt validation
- Error handling with fallback

**Security**:
- Private key never logged or exposed
- All transactions signed locally
- Supports dry-run mode for testing

---

### Polymarket Module

Prediction market integration and API client.

**Location**: `core/polymarket.py`

**PolymarketClient Class**:
```python
from core.polymarket import PolymarketClient

market_client = PolymarketClient()

# Get market data
market = await market_client.get_market("market_id")
# {
#     "id": "market_id",
#     "title": "Will Bitcoin reach $100k by 2025?",
#     "volume": 50000.0,
#     "created_at": "2024-01-01T00:00:00Z",
#     ...
# }

# Search for markets
markets = await market_client.search_markets("Bitcoin election", limit=10)

# Get order book
orderbook = await market_client.get_orderbook("market_id")

# Get best prices
prices = await market_client.get_best_prices("market_id")
# {
#     "yes_bid": 0.42,
#     "yes_ask": 0.44,
#     "no_bid": 0.56,
#     "no_ask": 0.58,
#     "mid_price": 0.43
# }

# Submit order (requires API key)
order = await market_client.submit_order(
    market_id="market_id",
    side="YES",
    amount=100.0,
    price=0.40,
    api_key="api_key"
)

# Auto-match news to market
market = await market_client.match_market_by_news(news_content)
```

**Features**:
- GraphQL API integration
- Automatic market matching
- Order book analysis
- Price discovery
- Cache optimization (5-minute market data, 1-minute orderbook)

---

## Integration Examples

### Basic Integration

```python
import asyncio
from core import (
    NewsStreamer,
    ProbabilityRouter,
    OpportunityFinder,
    Web3Signer,
    PolymarketClient,
)

async def main():
    streamer = NewsStreamer()
    brain = ProbabilityRouter()
    evaluator = OpportunityFinder()
    executor = Web3Signer()
    markets = PolymarketClient()

    async for news in streamer.stream_data():
        # Get probability
        prob, source = await brain.get_probability(news['title'])

        # Find market
        market = await markets.match_market_by_news(news['title'])
        if not market:
            continue

        # Get prices
        prices = await markets.get_best_prices(market['id'])

        # Evaluate
        should_bet, analysis = evaluator.should_bet(prob, prices['mid_price'])
        if not should_bet:
            continue

        # Execute
        success, tx = await executor.place_order(
            market['id'],
            100.0,
            'YES'
        )

asyncio.run(main())
```

---

## Error Handling

All modules include robust error handling:

```python
from core.logger import logger

try:
    prob, source = await brain.get_probability(content)
except Exception as e:
    logger.error(f"Probability calculation failed: {e}")
    prob = 0.5  # Fallback to neutral
```

---

## Performance Tuning

### Caching Strategy

```python
# Cache market data for 5 minutes
await cache_manager.set(f"market_{id}", market_data, ttl_seconds=300)

# Cache probabilities for 30 minutes
await cache_manager.set(f"prob_{content_hash}", probability, ttl_seconds=1800)
```

### Concurrent Operations

```python
# Fetch multiple markets in parallel
markets = await asyncio.gather(
    market_client.get_market("id1"),
    market_client.get_market("id2"),
    market_client.get_market("id3"),
)
```

---

## Configuration Reference

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete configuration options.

---

## Support

For questions or issues:
- GitHub Issues: https://github.com/fauzi69/PREDICTIVE-SNIPER/issues
- Documentation: https://github.com/fauzi69/PREDICTIVE-SNIPER/

---

**Last Updated**: May 2024
