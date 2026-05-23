import os
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Central configuration management with validation."""

    # WEB3 Config
    PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "").strip()
    POLYGON_RPC: str = os.getenv("POLYGON_RPC", "https://polygon-rpc.com/")
    USDC_CONTRACT: str = os.getenv(
        "USDC_CONTRACT", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    )

    # AI Platform Config
    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "").strip()
    MIMO_BASE_URL: str = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL: str = os.getenv("MIMO_MODEL", "mimo-v1")

    # Fallback AI Config
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")

    # Market Config
    POLYMARKET_API: str = os.getenv("POLYMARKET_API", "https://clob.polymarket.com")
    MIN_MARGIN: float = float(os.getenv("MIN_MARGIN", "0.20"))
    MAX_TRADE_SIZE: float = float(os.getenv("MAX_TRADE_SIZE", "1000"))

    # RSS Config
    RSS_UPDATE_INTERVAL: int = int(os.getenv("RSS_UPDATE_INTERVAL", "60"))
    MAX_NEWS_CACHE: int = int(os.getenv("MAX_NEWS_CACHE", "1000"))

    # Database Config
    CACHE_BACKEND: str = os.getenv("CACHE_BACKEND", "sqlite")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/sniper.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Logging Config
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/sniper.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "100"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Alert Config
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")

    # Security Config
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "60"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration values."""
        errors = []

        if not cls.MIMO_API_KEY:
            errors.append("❌ MIMO_API_KEY not set in .env")

        if not cls.GROQ_API_KEY:
            errors.append("⚠️ GROQ_API_KEY not set (fallback disabled)")

        if not cls.PRIVATE_KEY:
            errors.append("❌ PRIVATE_KEY not set in .env")

        if not cls.DRY_RUN and not cls.PRIVATE_KEY:
            errors.append("❌ Cannot run in live mode without PRIVATE_KEY")

        if cls.MIN_MARGIN < 0 or cls.MIN_MARGIN > 1:
            errors.append("❌ MIN_MARGIN must be between 0 and 1")

        if errors:
            for error in errors:
                logger.error(error)
            if any("❌" in e for e in errors):
                raise ValueError("Critical configuration missing")

        return True

    @classmethod
    def log_summary(cls):
        """Log configuration summary on startup."""
        logger.info("=" * 60)
        logger.info("🚀 MIMO PREDICTIVE SNIPER - CONFIGURATION")
        logger.info("=" * 60)
        logger.info(f"Network: Polygon ({cls.POLYGON_RPC[:30]}...)")
        logger.info(f"AI Engine: MIMO ({cls.MIMO_MODEL})")
        logger.info(f"Fallback: GROQ ({cls.GROQ_MODEL})")
        logger.info(f"Min Margin: {cls.MIN_MARGIN * 100}%")
        logger.info(f"Max Trade Size: {cls.MAX_TRADE_SIZE} USDC")
        logger.info(f"Dry Run Mode: {cls.DRY_RUN}")
        logger.info(f"Cache Backend: {cls.CACHE_BACKEND}")
        logger.info(f"Log Level: {cls.LOG_LEVEL}")
        logger.info("=" * 60)
