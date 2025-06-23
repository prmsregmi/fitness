"""
Cache module for request deduplication and response caching using Redis.
"""
import asyncio
import redis.asyncio as redis
import logging
import json
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

class RedisRequestCache:
    def __init__(self, cache_ttl: int = 3000):
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
            self._redis = None

    async def get_or_set(self, key: str, getter_func) -> Any:
        """
        Get value from Redis cache or set it using getter_func.
        Uses locks to prevent multiple simultaneous requests for the same key.
        """
        if self._redis is None:
            logger.warning("Redis is not available. Bypassing cache.")
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, getter_func)

        # Create or get lock for this key to prevent race conditions
        lock_key = f"lock:{key}"
        if lock_key not in self._locks:
            self._locks[lock_key] = asyncio.Lock()

        async with self._locks[lock_key]:
            # Check if we have a valid cached value
            cached_value = await self._redis.get(key)
            if cached_value:
                logger.info(f"Cache hit for key: {key}")
                return json.loads(cached_value)

            # If not, fetch new value using thread pool for sync functions
            logger.info(f"Cache miss for key: {key}, fetching new value")
            loop = asyncio.get_event_loop()
            new_value = await loop.run_in_executor(None, getter_func)
            
            # Store the new value in Redis with an expiration
            serialized_value = json.dumps(new_value)
            await self._redis.set(key, serialized_value, ex=self._cache_ttl)
            
            return new_value

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