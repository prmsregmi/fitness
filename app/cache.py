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
    def __init__(self, cache_ttl: int = 3600):
        """
        Initializes the Redis cache.
        Connects to Redis using environment variables.
        """
        self._redis: Optional[redis.Redis] = None
        self._locks: dict[str, asyncio.Lock] = {}
        self._cache_ttl = cache_ttl
        self.connect()

    def connect(self):
        """Establishes a connection to the Redis server."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self._redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=False)
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise ConnectionError("Redis is not available")

    async def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        if self._redis:
            await self._redis.delete(key)
            logger.info(f"Invalidated cache for key: {key}")

    async def clear(self) -> None:
        """Clear all cache entries from the Redis database (use with caution)."""
        if self._redis:
            await self._redis.flushdb()
            logger.info("Cleared entire Redis cache")

# Global cache instance
request_cache = RedisRequestCache() 