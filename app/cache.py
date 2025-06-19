"""
Cache module for request deduplication and response caching.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RequestCache:
    def __init__(self, cache_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._cache_ttl = cache_ttl

    async def get_or_set(self, key: str, getter_func) -> Any:
        """
        Get value from cache or set it using getter_func.
        Uses locks to prevent multiple simultaneous requests for the same key.
        
        Args:
            key: Cache key
            getter_func: Async function to call if key not in cache
        
        Returns:
            Cached or newly fetched value
        """
        # Create or get lock for this key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        
        async with self._locks[key]:
            # Check if we have a valid cached value
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.info(f"Cache hit for key: {key}")
                    return value
            
            # If we get here, we need to fetch new value
            logger.info(f"Cache miss for key: {key}, fetching new value")
            value = await getter_func()
            self._cache[key] = (time.time(), value)
            return value

    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Invalidated cache for key: {key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cleared entire cache")

# Global cache instance
request_cache = RequestCache() 