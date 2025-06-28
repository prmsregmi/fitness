"""
User service for handling user identification and request history.
"""

import uuid
import json
import logging
from typing import List
from fastapi import Request, Response
from datetime import datetime, UTC

from ..cache import request_cache
from ..models.requests import RequestHistoryItem, UserHistoryResponse
from ..models.database import SessionLocal, User, Task, SearchRequest

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
    async def get_user_history(user_id: str) -> UserHistoryResponse:
        """
        Get all tasks and their search requests for a specific user_id.
        The user_id should match the User.id in the database.
        """
        try:
            requests_history = []
            
            db = SessionLocal()
            try:
                # Find the user by ID (user_id should match User.id)
                # Convert string UUID to UUID object for database query
                user_uuid = uuid.UUID(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                
                if not user:
                    logger.info(f"User {user_id} not found in database - new user")
                    return UserHistoryResponse(
                        user_id=user_id,
                        total_requests=0,
                        recent_requests=[],
                        message="No completed search history found - you're a new user!"
                    )
                
                # Get all tasks for this user
                tasks = db.query(Task).filter(Task.user_id == user.id).all()
                logger.info(f"Found {len(tasks)} tasks for user {user_id}")
                
                # For each task, get all its search requests
                for task in tasks:
                    search_requests = db.query(SearchRequest).filter(SearchRequest.task_id == task.id).all()
                    
                    for search_request in search_requests:
                        try:
                            # Parse the result JSON
                            result = json.loads(search_request.result)
                            
                            # Create request history item
                            requests_history.append(RequestHistoryItem(
                                query=search_request.query,
                                result=result,
                                timestamp=search_request.created_at.isoformat(),
                                request_id=search_request.id,  # This is the hex hash
                                status=search_request.status,
                                completed_at=search_request.completed_at.isoformat() if search_request.completed_at else None
                            ))
                            
                        except Exception as e:
                            logger.error(f"Error processing search request {search_request.id}: {e}")
                            continue
                
                # Also check Redis for any pending requests that might belong to this user
                # await UserService._add_redis_pending_requests(user_id, requests_history)
                
                # Sort by timestamp (most recent first)
                requests_history.sort(
                    key=lambda x: x.timestamp if x.timestamp else "1900-01-01T00:00:00",
                    reverse=True
                )
                
                return UserHistoryResponse(
                    user_id=user_id,
                    total_requests=len(requests_history),
                    recent_requests=requests_history,
                    message=(
                        f"Found {len(requests_history)} search requests across {len(tasks)} tasks" 
                        if requests_history 
                        else "No completed search history found"
                    )
                )
            
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving user history for {user_id}: {str(e)}")
            logger.exception("Full exception details:")
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=0,
                recent_requests=[],
                message="Error retrieving search history"
            )
    
    @staticmethod
    async def _add_redis_pending_requests(user_id: str, requests_history: List[RequestHistoryItem]) -> None:
        """Add any pending requests from Redis cache that might belong to this user."""
        try:
            if not request_cache._redis:
                return
            
            # Get all keys from the "searches" hash
            hash_key = "searches"
            all_fields = await request_cache.hkeys(hash_key)
            
            existing_hashes = {item.request_id for item in requests_history}
            
            for field in all_fields:
                try:
                    if isinstance(field, bytes):
                        field = field.decode('utf-8')
                    
                    # Skip if we already have this request from DB
                    if field in existing_hashes:
                        continue
                    
                    cached_result = await request_cache.hget(hash_key, field)
                    if cached_result:
                        if isinstance(cached_result, bytes):
                            cached_result = cached_result.decode('utf-8')
                        
                        result = json.loads(cached_result)
                        status = result.get("status", "unknown")
                        
                        if status in ["pending", "failed"]:
                            requests_history.append(RequestHistoryItem(
                                query=result.get("query", f"Search {field[:8]}"),
                                result=result.get("result") if status == "completed" else {"status": status, "message": result.get("error", "In progress...")},
                                timestamp=result.get("timestamp", "unknown"),
                                request_id=field,
                                status=status,
                                completed_at=result.get("completed_at")
                            ))
                            
                except Exception as e:
                    logger.error(f"Error processing Redis field {field}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error adding Redis pending requests: {e}")
    
    @staticmethod
    def get_or_create_user_in_db(user_id: str) -> User:
        """Get existing user from database or create a new one with the specified user_id."""
        db = SessionLocal()
        try:
            # Convert string UUID to UUID object for database operations
            user_uuid = uuid.UUID(user_id)
            
            # Try to find existing user
            user = db.query(User).filter(User.id == user_uuid).first()
            
            if user:
                # Update last_active timestamp
                user.last_active = datetime.now(UTC)
                db.commit()
                logger.info(f"Found existing user: {user_id}")
                return user
            
            # Create new user with the specified ID
            user = User(id=user_uuid)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user in database: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user {user_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close() 