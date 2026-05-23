import json
import sqlite3
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional
import asyncio
from core.config import Config
from core.logger import logger

try:
    import redis
except ImportError:
    redis = None


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache."""
        pass


class SqliteCache(CacheBackend):
    """SQLite-based cache backend."""

    def __init__(self, db_path: str = Config.SQLITE_DB_PATH):
        self.db_path = db_path
        import os
        os.makedirs(os.path.dirname(db_path) or "data", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)"
            )
            conn.commit()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value FROM cache WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (key, datetime.utcnow()),
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            expires_at = (
                datetime.utcnow() + timedelta(seconds=ttl_seconds)
                if ttl_seconds > 0
                else None
            )
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, json.dumps(value), expires_at),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM cache WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (key, datetime.utcnow()),
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def cleanup_expired(self):
        """Remove expired entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (datetime.utcnow(),),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


class RedisCache(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, redis_url: str = Config.REDIS_URL):
        if not redis:
            raise ImportError("redis library required for Redis backend")
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            self.redis.setex(key, ttl_seconds, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache."""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False


class CacheManager:
    """Smart cache manager with automatic backend selection."""

    def __init__(self):
        if Config.CACHE_BACKEND == "redis":
            try:
                self.backend = RedisCache()
                logger.info("✅ Redis cache backend initialized")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}. Falling back to SQLite")
                self.backend = SqliteCache()
        else:
            self.backend = SqliteCache()
            logger.info("✅ SQLite cache backend initialized")

    def hash_key(self, content: str) -> str:
        """Generate cache key from content."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_or_fetch(
        self, key: str, fetch_func, ttl_seconds: int = 3600
    ) -> Any:
        """Get from cache or fetch if not exists."""
        # Try to get from cache
        cached = await self.backend.get(key)
        if cached is not None:
            logger.debug(f"📦 Cache hit: {key}")
            return cached

        # Fetch and cache
        logger.debug(f"📦 Cache miss: {key}. Fetching...")
        value = await fetch_func()
        if value is not None:
            await self.backend.set(key, value, ttl_seconds)
        return value

    async def get(self, key: str) -> Optional[Any]:
        return await self.backend.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        return await self.backend.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> bool:
        return await self.backend.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.backend.exists(key)


# Global cache manager instance
cache_manager = CacheManager()
