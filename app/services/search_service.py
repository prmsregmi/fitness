"""
Search service for handling search-related business logic.
"""

import time
import logging
from typing import Any

from ..cache import request_cache

logger = logging.getLogger(__name__)


def mock_api(query: str) -> dict:
    """Mock API function for testing purposes."""
    logger.info(query, " is received.")
    time.sleep(8)
    return {"message": "API worked."}


class SearchService:
    """Service for search operations and caching."""
    
    @staticmethod
    async def perform_search(query: str, force_refresh: bool = False) -> Any:
        """
        Perform a search query with caching and proper error handling.
        
        Args:
            query: The search query
            force_refresh: Whether to bypass cache and force a fresh request
            
        Returns:
            Search results
        """
        logger.info(f"Processing search request with query: {query}")
        
        try:
            # If force refresh, invalidate the cache for this query
            if force_refresh:
                await request_cache.invalidate(query)
            
            # Use the cache to handle the request
            # The external API (mock_api) will run in a thread pool via cache
            # In the future, replace mock_api with actual API calls like:
            # result = await request_cache.get_or_set(
            #     query,
            #     lambda: future_house_crow_api(query)
            # )
            result = await request_cache.get_or_set(
                query,
                lambda: mock_api(query)
            )
            
            logger.info("Successfully processed search request")
            return result
            
        except Exception as e:
            logger.error(f"Error in search service: {str(e)}")
            # Return a structured error response instead of raising
            return {
                "error": "Search service unavailable",
                "message": "Please try again later",
                "query": query
            } 