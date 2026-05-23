# MIMO Predictive Sniper - Deployment Guide

## Prerequisites

- Docker & Docker Compose (for containerized deployment)
- Python 3.10+ (for local deployment)
- Polygon wallet with private key
- MIMO AI API key (from https://platform.xiaomimimo.com/)
- GROQ API key (optional, from https://console.groq.com/)

## Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
git clone https://github.com/fauzi69/PREDICTIVE-SNIPER.git
cd PREDICTIVE-SNIPER
cp .env.example .env
```

### 2. Configure `.env` File

Edit `.env` with your credentials:

```env
# Required
PRIVATE_KEY=0x...your_private_key...
MIMO_API_KEY=your_mimo_key...

# Optional but recommended
GROQ_API_KEY=your_groq_key...

# Deployment
DRY_RUN=true  # Set to false for live trading
CACHE_BACKEND=redis
LOG_LEVEL=INFO
```

### 3. Run with Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f sniper

# Stop
docker-compose down
```

## Local Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Directly

```bash
python main.py
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRIVATE_KEY` | - | Polygon wallet private key (required) |
| `MIMO_API_KEY` | - | Xiaomi MIMO API key (required) |
| `MIMO_BASE_URL` | `https://api.xiaomimimo.com/v1` | MIMO API endpoint |
| `GROQ_API_KEY` | - | Groq API key (fallback) |
| `POLYGON_RPC` | `https://polygon-rpc.com/` | Polygon RPC endpoint |
| `MIN_MARGIN` | `0.20` | Minimum edge to place bet (20%) |
| `MAX_TRADE_SIZE` | `1000` | Max USDC per trade |
| `DRY_RUN` | `true` | Disable real transactions |
| `CACHE_BACKEND` | `sqlite` | Cache: `sqlite` or `redis` |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

### Redis Configuration

For production, use Redis for distributed caching:

```env
CACHE_BACKEND=redis
REDIS_URL=redis://redis:6379/0
```

Docker Compose automatically sets up Redis.

## Testing

Run unit tests:

```bash
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov-report=html
```

## Performance Tuning

### For High-Volume Trading

```env
# Increase cache size
MAX_NEWS_CACHE=5000

# Faster market polling
RSS_UPDATE_INTERVAL=30

# Optimize gas
POLYGON_RPC=https://rpc-mainnet.maticvigil.com/
```

### For Low-Cost Testing

```env
DRY_RUN=true
MIN_MARGIN=0.10  # Lower margin threshold
MAX_TRADE_SIZE=10  # Test with small amounts
```

## Monitoring

### Check Logs

```bash
# Local
tail -f logs/sniper.log

# Docker
docker-compose logs -f sniper
```

### View Statistics

The sniper logs trading statistics on shutdown:

```
📊 FINAL STATISTICS
Total Trades: 5
Total Volume: 1500.50 USDC
Avg Trade Size: 300.10 USDC
```

## Production Deployment

### VPS Deployment

1. **Install Docker:**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

2. **Clone repository:**

```bash
cd /opt && git clone https://github.com/fauzi69/PREDICTIVE-SNIPER.git
cd PREDICTIVE-SNIPER
```

3. **Setup and run:**

```bash
cp .env.example .env
# Edit .env with production credentials

# Start as service
docker-compose up -d
```

4. **Enable auto-restart:**

```bash
# Docker handles this with 'restart: unless-stopped'
docker-compose ps  # Verify it's running
```

### Monitoring & Alerts

For Discord/Telegram alerts (coming soon):

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=your_token_here
```

## Security Best Practices

1. **Never commit `.env` file** - Always use `.env.example`
2. **Use a burner wallet** - Test with small amounts first
3. **Enable dry-run mode** - Test with `DRY_RUN=true` first
4. **Restrict permissions** - Keep private keys secure
5. **Use environment-specific secrets** - Don't hardcode credentials

## Troubleshooting

### "Connection refused" on Polygon RPC

Try alternative RPC:
```env
POLYGON_RPC=https://rpc-mainnet.maticvigil.com/
```

### MIMO API Rate Limited

Groq fallback should handle this. Check logs:
```bash
grep -i "rate limit" logs/sniper.log
```

### Insufficient USDC Balance

Check balance before trading:
```bash
docker-compose exec sniper python -c "from core.execution import Web3Signer; Web3Signer().get_balance()"
```

### Redis Connection Failed

Use SQLite instead:
```env
CACHE_BACKEND=sqlite
```

## Support

- GitHub Issues: https://github.com/fauzi69/PREDICTIVE-SNIPER/issues
- Documentation: https://github.com/fauzi69/PREDICTIVE-SNIPER/README.md

---

**Built for the Future of Decentralized Finance.**
