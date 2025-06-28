"""
Search service for handling search-related business logic.
"""
import time
import logging
from core.examples.future_house import future_house_crow_api
import hashlib
import json
import asyncio
from datetime import datetime
from futurehouse_client import PQATaskResponse

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
    async def start_search(query: str, force_refresh: bool = False) -> dict:
        """
        Start a search query asynchronously. Returns immediately with task status.
        """
        logger.info(f"Starting search request with query: {query}")
        query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        hash_key = "searches"  # Main hash key
        field_key = query_hash  # Field within the hash
        
        try:
            # Check if we have a valid cached value
            if not force_refresh:
                cached_value = await request_cache.hget(hash_key, field_key)
                if cached_value:
                    logger.info(f"Cache hit for hash key: {hash_key}, field: {field_key}")
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
            
            logger.info(f"Starting background search for hash key: {hash_key}, field: {field_key}")
            current_time = datetime.now()
            
            # Start API call immediately for maximum speed
            task = asyncio.create_task(
                SearchService._execute_search_background(query, query_hash, hash_key, field_key, current_time)
            )
            SearchService._background_tasks[query_hash] = task
            
            # Store pending request in cache (while API runs in background)
            pending_request = {
                "query": query,
                "result": None,
                "status": "pending",
                "timestamp": current_time.isoformat()
            }
            
            pending_serialized = json.dumps(pending_request)
            await request_cache.hset(hash_key, field_key, pending_serialized)
            
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
    async def _execute_search_background(query: str, query_hash: str, hash_key: str, field_key: str, start_time: datetime):
        """Execute the actual search in the background."""
        try:
            logger.info(f"Executing background search for query: {query}")
            
            # Run the blocking API call in a thread executor
            loop = asyncio.get_running_loop()
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
            await request_cache.hset(hash_key, field_key, serialized_value)
            
            logger.info(f"Background search completed for query: {query}")
            
            # Direct database write after cache update (no signals)
            await SearchService._sync_to_database(query_hash, query, result)
            
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
            await request_cache.hset(hash_key, field_key, error_serialized)
            
        finally:
            # Clean up the background task reference
            if query_hash in SearchService._background_tasks:
                del SearchService._background_tasks[query_hash]

    @staticmethod
    async def _sync_to_database(query_hash: str, query: str, result: dict):
        """Sync completed search result to database."""
        try:
            # Run database operations in thread executor to avoid blocking
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, 
                SearchService._perform_db_sync,
                query_hash,
                query, 
                result
            )
            logger.info(f"Search result synced to database: {query_hash}")
            
        except Exception as e:
            logger.error(f"Failed to sync search to database: {e}")
    
    @staticmethod
    def _perform_db_sync(query_hash: str, query: str, result: dict):
        """Perform the actual database sync (runs in thread executor)."""
        from .database_service import DatabaseService
        from ..models.database import SessionLocal
        
        db = SessionLocal()
        try:
            logger.info(f"Starting DB sync for query_hash: {query_hash}")
            
            # Create new user and task for each search
            user, task = DatabaseService.create_user_and_task(db)
            logger.info(f"Created user {user.id} and task {task.id}")
            
            # Store the search request with hex hash as ID
            search_request = DatabaseService.store_search_request(
                db=db,
                query_hash=query_hash,
                task_id=task.id,  # Pass UUID directly, not string
                query=query,
                result=result,
                status="completed"
            )
            
            if search_request:
                logger.info(f"Successfully created search request: {search_request.id}")
            else:
                logger.error("Failed to create search request - returned None")
                
        except Exception as e:
            logger.error(f"Exception in _perform_db_sync: {e}")
            logger.exception("Full exception details:")
        finally:
            db.close()

    @staticmethod
    async def get_search_status(task_id: str) -> dict:
        """
        Get the status of a search task.
        """
        hash_key = "searches"  # Main hash key
        field_key = task_id    # Field within the hash
        
        try:
            cached_value = await request_cache.hget(hash_key, field_key)
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