"""
User service for handling user identification and request history.
"""

import uuid
import logging
from datetime import datetime
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
    
    @staticmethod
    async def store_pending_request(user_id: str, query: str) -> str:
        """Store a pending request immediately when request starts."""
        current_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        # Check if user made the same query within 15 minutes
        user_requests_key = f"user_requests:{user_id}"
        try:
            existing_requests = await request_cache.get_or_set(user_requests_key, lambda: [])
            if not isinstance(existing_requests, list):
                existing_requests = []
        except Exception:
            existing_requests = []
        
        # Check recent requests for duplicate query
        for existing_request_id in existing_requests[-10:]:  # Check last 10 requests
            request_key = f"request:{user_id}:{existing_request_id}"
            try:
                request_data = await request_cache.get_or_set(request_key, lambda: None)
                if request_data and request_data.get('query') == query:
                    # Check if within 15 minutes and not pending
                    request_time = datetime.fromisoformat(request_data['timestamp'])
                    time_diff = (current_time - request_time).total_seconds() / 60
                    if time_diff <= 15 and request_data.get('status') != 'pending':
                        logger.info("Duplicate query within 15 minutes, not storing new request")
                        return existing_request_id  # Return existing request ID
            except Exception:
                continue
        
        # Store new pending request
        request_data = {
            "query": query,
            "result": None,
            "status": "pending",
            "timestamp": current_time.isoformat(),
            "request_id": request_id
        }
        
        # Store individual request
        request_key = f"request:{user_id}:{request_id}"
        await request_cache.get_or_set(request_key, lambda: request_data)
        
        # Update user's request list
        existing_requests.append(request_id)
        # Keep only last 50 requests
        existing_requests = existing_requests[-50:]
        
        # Force update the user requests list
        await request_cache.invalidate(user_requests_key)
        await request_cache.get_or_set(user_requests_key, lambda: existing_requests)
        
        logger.info(f"Stored pending request: {request_id}")
        return request_id
    
    @staticmethod
    async def update_request_with_result(user_id: str, request_id: str, result: dict) -> None:
        """Update a pending request with the actual result."""
        try:
            request_key = f"request:{user_id}:{request_id}"
            
            # Get existing request data
            existing_data = await request_cache.get_or_set(request_key, lambda: None)
            if not existing_data:
                logger.warning(f"Request {request_id} not found for update")
                return
            
            # Update with result
            existing_data["result"] = result
            existing_data["status"] = "completed"
            existing_data["completed_at"] = datetime.now().isoformat()
            
            # Force update in cache
            await request_cache.invalidate(request_key)
            await request_cache.get_or_set(request_key, lambda: existing_data)
            
            logger.info(f"Updated request {request_id} with result")
            
        except Exception as e:
            logger.error(f"Error updating request {request_id}: {str(e)}")
    
    @staticmethod
    async def store_user_request(user_id: str, query: str, result: dict) -> None:
        """Store user request in cache for history tracking (legacy method)."""
        # For backward compatibility, create and immediately complete request
        request_id = await UserService.store_pending_request(user_id, query)
        await UserService.update_request_with_result(user_id, request_id, result)
    
    @staticmethod
    async def get_user_history(user_id: str) -> UserHistoryResponse:
        """Get user's request history."""
        try:
            # Get user's request list
            user_requests_key = f"user_requests:{user_id}"
            request_ids = await request_cache.get_or_set(user_requests_key, lambda: [])
            
            # Get detailed request data
            requests_history = []
            for request_id in request_ids[-10:]:  # Show last 10 requests
                request_key = f"request:{user_id}:{request_id}"
                try:
                    request_data = await request_cache.get_or_set(request_key, lambda: None)
                    if request_data:
                        requests_history.append(RequestHistoryItem(**request_data))
                except Exception:
                    continue
            
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=len(request_ids),
                recent_requests=requests_history,
                message="Welcome to your request history!"
            )
        except Exception as e:
            logger.error(f"Error retrieving user history: {str(e)}")
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=0,
                recent_requests=[],
                message="Welcome! No request history yet."
            ) 