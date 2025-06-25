"""
User service for handling user identification and request history.
"""

import uuid
import json
import logging
from typing import List, Optional
from fastapi import Request, Response

from ..cache import request_cache
from ..models.requests import RequestHistoryItem, UserHistoryResponse

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and request tracking."""
    
    @staticmethod
    def get_or_create_user_id(request: Request, response: Response) -> str:
        """Get user ID from cookie or create a new one."""
        user_id = request.cookies.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
            response.set_cookie("user_id", user_id, max_age=5*24*60*60)  # 5 days
            logger.info(f"Created new user ID: {user_id}")
        return user_id
    
    #TODO: load_old is not used as of now.
    @staticmethod
    async def get_user_history(user_id: str, load_old: bool = False) -> UserHistoryResponse:
        """Get all existing cached data for the user."""
        try:
            requests_history = []
            
            # Get all cached search results for this user
            if request_cache._redis:
                pattern = f"search:{user_id}:*"
                keys = await request_cache._redis.keys(pattern)
                
                for key in keys:
                    try:
                        # Convert key to string if it's bytes
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        
                        cached_result = await request_cache._redis.get(key)
                        if cached_result:
                            # Parse the cached result
                            if isinstance(cached_result, bytes):
                                cached_result = cached_result.decode('utf-8')
                            
                            result = json.loads(cached_result) if isinstance(cached_result, str) else cached_result
                            
                            # Extract query hash from key
                            query_hash = key_str.split(":")[-1]
                            
                            # Get the actual query from the cached result
                            actual_query = result.get("query", f"Search {query_hash[:8]}")
                            search_status = result.get("status", "unknown")
                            timestamp = result.get("timestamp", "unknown")
                            completed_at = result.get("completed_at")
                            
                            # Build request history item based on status
                            if search_status == "completed":
                                search_result = result.get("result")
                                display_timestamp = completed_at or timestamp
                            elif search_status == "pending":
                                search_result = {"status": "pending", "message": "Search in progress..."}
                                display_timestamp = timestamp
                            elif search_status == "failed":
                                search_result = {"status": "failed", "error": result.get("error", "Unknown error")}
                                display_timestamp = completed_at or timestamp
                            else:
                                search_result = result
                                display_timestamp = timestamp
                            
                            requests_history.append(RequestHistoryItem(
                                query=actual_query,
                                result=search_result,
                                timestamp=display_timestamp,
                                request_id=query_hash,
                                status=search_status,
                                completed_at=completed_at
                            ))
                    except Exception as e:
                        logger.error(f"Error processing cached key {key}: {e}")
                        continue
                
                # Sort by timestamp (most recent first)
                requests_history.sort(
                    key=lambda x: x.timestamp if x.timestamp != "unknown" else "1900-01-01T00:00:00", 
                    reverse=True
                )
            
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=len(requests_history),
                recent_requests=requests_history,
                message="Your search history" if requests_history else "No search history found"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving cached data: {str(e)}")
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=0,
                recent_requests=[],
                message="Error retrieving search history"
            ) 