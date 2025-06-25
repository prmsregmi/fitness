"""
Search service for handling search-related business logic.
"""

import time
import logging
from typing import Any, Optional
import hashlib
import json
import asyncio
from datetime import datetime

from ..cache import request_cache

logger = logging.getLogger(__name__)


def mock_api(query: str) -> dict:
    """Mock API function for testing purposes."""
    logger.info(f"{query} is received.")
    time.sleep(10)
    return {"message": "API worked.", "query": query, "timestamp": datetime.now().isoformat()}


class SearchService:
    """Service for search operations and caching."""
    
    _background_tasks = {}  # Track running background tasks

    @staticmethod
    async def start_search(user_id: str, query: str, force_refresh: bool = False) -> dict:
        """
        Start a search query asynchronously. Returns immediately with task status.
        """
        logger.info(f"Starting search request with query: {query}")
        query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        cache_key = f"search:{user_id}:{query_hash}"
        
        try:
            # Check if we have a valid cached value
            if not force_refresh:
                cached_value = await request_cache._redis.get(cache_key)
                if cached_value:
                    logger.info(f"Cache hit for key: {cache_key}")
                    cached_data = json.loads(cached_value)
                    if cached_data.get("status") == "completed":
                        return {
                            "task_id": query_hash,
                            "status": "completed",
                            "result": cached_data.get("result"),
                            "from_cache": True
                        }
            
            # Check if task is already running
            if query_hash in SearchService._background_tasks:
                task = SearchService._background_tasks[query_hash]
                if not task.done():
                    return {
                        "task_id": query_hash,
                        "status": "pending",
                        "message": "Search is already in progress",
                        "from_cache": False
                    }
            
            logger.info(f"Starting background search for: {cache_key}")
            current_time = datetime.now()
            
            # Store pending request immediately
            pending_request = {
                "query": query,
                "result": None,
                "status": "pending",
                "timestamp": current_time.isoformat()
            }
            
            pending_serialized = json.dumps(pending_request)
            await request_cache._redis.set(cache_key, pending_serialized, ex=request_cache._cache_ttl)
            
            # Start background task
            task = asyncio.create_task(
                SearchService._execute_search_background(user_id, query, query_hash, cache_key, current_time)
            )
            SearchService._background_tasks[query_hash] = task
            
            return {
                "task_id": query_hash,
                "status": "pending",
                "message": "Search started successfully",
                "from_cache": False
            }
            
        except Exception as e:
            logger.error(f"Error starting search: {str(e)}")
            return {
                "task_id": query_hash if 'query_hash' in locals() else None,
                "status": "failed",
                "error": "Failed to start search",
                "message": str(e)
            }

    @staticmethod
    async def _execute_search_background(user_id: str, query: str, query_hash: str, cache_key: str, start_time: datetime):
        """Execute the actual search in the background."""
        try:
            logger.info(f"Executing background search for query: {query}")
            
            # Run the blocking API call in a thread executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, mock_api, query)
            
            # Update cache with completed result
            completed_request = {
                "query": query,
                "result": result,
                "status": "completed",
                "timestamp": start_time.isoformat(),
                "completed_at": datetime.now().isoformat()
            }
            
            serialized_value = json.dumps(completed_request)
            await request_cache._redis.set(cache_key, serialized_value, ex=request_cache._cache_ttl)
            
            logger.info(f"Background search completed for query: {query}")
            
        except Exception as e:
            logger.error(f"Background search failed for query {query}: {str(e)}")
            
            # Update cache with error
            error_request = {
                "query": query,
                "result": None,
                "status": "failed",
                "timestamp": start_time.isoformat(),
                "completed_at": datetime.now().isoformat(),
                "error": str(e)
            }
            
            error_serialized = json.dumps(error_request)
            await request_cache._redis.set(cache_key, error_serialized, ex=request_cache._cache_ttl)
            
        finally:
            # Clean up the background task reference
            if query_hash in SearchService._background_tasks:
                del SearchService._background_tasks[query_hash]

    @staticmethod
    async def get_search_status(user_id: str, task_id: str) -> dict:
        """
        Get the status of a search task.
        """
        cache_key = f"search:{user_id}:{task_id}"
        
        try:
            cached_value = await request_cache._redis.get(cache_key)
            if not cached_value:
                return {
                    "task_id": task_id,
                    "status": "not_found",
                    "message": "Search task not found"
                }
            
            result = json.loads(cached_value)
            status = result.get("status", "unknown")
            
            response = {
                "task_id": task_id,
                "status": status,
                "query": result.get("query"),
                "timestamp": result.get("timestamp")
            }
            
            if status == "completed":
                response["result"] = result.get("result")
                response["completed_at"] = result.get("completed_at")
            elif status == "failed":
                response["error"] = result.get("error")
                response["completed_at"] = result.get("completed_at")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting search status: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": str(e)
            }