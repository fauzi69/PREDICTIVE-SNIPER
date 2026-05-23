# Contributing to MIMO Predictive Sniper

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/fauzi69/PREDICTIVE-SNIPER.git
cd PREDICTIVE-SNIPER
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -r requirements.txt
pip install -e .  # Install in editable mode
```

### 4. Setup Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Code Style

We follow PEP 8 with some additions:

- **Line length**: 100 characters max
- **Formatter**: Black
- **Linter**: Flake8
- **Type checking**: Mypy

### Run Code Quality Checks

```bash
# Format code
black core main.py tests/

# Lint
flake8 core main.py tests/

# Type check
mypy core
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=core --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_core.py::TestNewsStreamer -v
```

## Project Structure

```
PREDICTIVE-SNIPER/
├── core/
│   ├── __init__.py
│   ├── brain.py          # AI probability router
│   ├── cache.py          # Caching layer (SQLite/Redis)
│   ├── config.py         # Configuration management
│   ├── evaluator.py      # Market opportunity finder
│   ├── execution.py      # Web3 transaction execution
│   ├── ingestion.py      # News feed streaming
│   ├── logger.py         # Logging configuration
│   └── polymarket.py     # Polymarket API client
├── tests/
│   ├── __init__.py
│   └── test_core.py      # Unit tests
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── .env.example          # Environment template
├── DEPLOYMENT.md         # Deployment guide
└── README.md             # Project documentation
```

## Adding New Features

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write Tests First (TDD)

```python
# tests/test_new_feature.py
def test_new_feature():
    assert new_feature() == expected_output
```

### 3. Implement Feature

```python
# core/new_module.py
def new_feature():
    return expected_output
```

### 4. Add Documentation

Update docstrings and README as needed.

### 5. Run Tests & Quality Checks

```bash
pytest tests/ -v
black core main.py
flake8 core main.py
mypy core
```

### 6. Commit & Push

```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### 7. Create Pull Request

Create PR on GitHub with:
- Clear title
- Detailed description
- Link to relevant issues
- Test coverage proof

## Module Documentation

### Config Module

```python
from core.config import Config

# Access configuration
print(Config.MIN_MARGIN)
print(Config.POLYGON_RPC)

# Validate config
Config.validate()
Config.log_summary()
```

### Logger Module

```python
from core.logger import logger

logger.info("Application started")
logger.warning("Something needs attention")
logger.error("An error occurred")
logger.debug("Debug information")
```

### Cache Module

```python
from core.cache import cache_manager

# Set value
await cache_manager.set("key", {"data": value}, ttl_seconds=3600)

# Get value
data = await cache_manager.get("key")

# Check existence
exists = await cache_manager.exists("key")

# Delete key
await cache_manager.delete("key")
```

### Brain Module

```python
from core.brain import ProbabilityRouter

brain = ProbabilityRouter()
probability, source = await brain.get_probability("News content here")
# Returns: (float between 0-1, "MIMO" or "GROQ")
```

### Evaluator Module

```python
from core.evaluator import OpportunityFinder

evaluator = OpportunityFinder(min_margin=0.20)

# Check if opportunity exists
should_bet, analysis = evaluator.should_bet(ai_prob=0.70, market_price=0.40)

# Calculate bet amount
amount = evaluator.calculate_bet_amount(analysis, available_balance=1000)

# Record trade
evaluator.record_trade(market_id, ai_prob, market_price, amount, "YES")

# Get stats
stats = evaluator.get_performance_stats()
```

### Polymarket Module

```python
from core.polymarket import PolymarketClient

market_client = PolymarketClient()

# Get market data
market = await market_client.get_market("market_id")

# Search markets
markets = await market_client.search_markets("Bitcoin election")

# Get prices
prices = await market_client.get_best_prices("market_id")
# Returns: {yes_bid, yes_ask, no_bid, no_ask, mid_price}
```

## Common Issues & Solutions

### Import Errors

```python
# Make sure core/__init__.py exports modules
from core import ProbabilityRouter, OpportunityFinder
```

### Async/Await Issues

All async functions must be called with `await`:

```python
# ❌ Wrong
probability = brain.get_probability(text)

# ✅ Correct
probability = await brain.get_probability(text)
```

### Configuration Not Loading

```bash
# Make sure .env file exists and has correct permissions
ls -la .env
chmod 600 .env
```

## Performance Optimization

### Caching

Use Redis for distributed caching:

```python
# Set Redis backend
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

### Async I/O

All network calls are async. Batch requests when possible:

```python
# Get multiple markets concurrently
markets = await asyncio.gather(
    market_client.get_market("id1"),
    market_client.get_market("id2"),
    market_client.get_market("id3"),
)
```

## Debugging

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### Use IPython REPL

```bash
ipython
```

```python
from core import *
market_client = PolymarketClient()
# Test calls interactively
```

## Release Process

1. Update version in `core/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will auto-create release

## Questions?

- Open an issue on GitHub
- Check existing documentation
- Review test cases for usage examples

---

Happy coding! 🚀
