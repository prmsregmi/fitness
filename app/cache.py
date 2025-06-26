"""
Cache module for request deduplication and response caching using Redis.
"""
import asyncio
import redis.asyncio as redis
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class RedisRequestCache:
    def __init__(self):
        """
        Initializes the Redis cache.
        Connects to Redis using environment variables.
        """
        self._redis: Optional[redis.Redis] = None
        self._locks: dict[str, asyncio.Lock] = {}
        self.connect()

    def connect(self):
        """Establishes a connection to the Redis server and sets memory/policy."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self._redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=False)
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")

            # We'll set the config when the Redis connection is first used
            # This avoids event loop issues during module import
            self._config_set = False
        except Exception as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise ConnectionError("Redis is not available")

    async def _ensure_config_set(self) -> None:
        """Ensure Redis configuration is set (called on first use)."""
        if self._redis and not self._config_set:
            try:
                await self._redis.config_set("maxmemory", "250mb")
                await self._redis.config_set("maxmemory-policy", "allkeys-lru")
                self._config_set = True
                logger.info("Set Redis maxmemory to 250mb and maxmemory-policy to allkeys-lru")
            except Exception as e:
                logger.warning(f"Could not set Redis config: {e}")

    async def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        if self._redis:
            await self._ensure_config_set()
            await self._redis.delete(key)
            logger.info(f"Invalidated cache for key: {key}")

    async def clear(self) -> None:
        """Clear all cache entries from the Redis database (use with caution)."""
        if self._redis:
            await self._ensure_config_set()
            await self._redis.flushdb()
            logger.info("Cleared entire Redis cache")

    async def hget(self, name: str, key: str):
        """Get value from hash with auto-config."""
        if self._redis:
            await self._ensure_config_set()
            return await self._redis.hget(name, key)
        return None

    async def hset(self, name: str, key: str, value: str):
        """Set value in hash with auto-config."""
        if self._redis:
            await self._ensure_config_set()
            return await self._redis.hset(name, key, value)
        return None

# Global cache instance
request_cache = RedisRequestCache() 