"""
Database service for handling persistent data operations.
"""

import json
import logging
from datetime import datetime, timedelta, UTC
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.database import SessionLocal, User, UserRequest, SearchCache
from ..models.requests import RequestHistoryItem, UserHistoryResponse

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""
    
    @staticmethod
    def get_db() -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            pass  # Don't close here, let caller handle it
    
    @staticmethod
    def get_or_create_user(db: Session, user_id: str) -> User:
        """Get existing user or create a new one."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user in database: {user_id}")
        else:
            # Update last active
            user.last_active = datetime.now(UTC)
            db.commit()
        return user
    
    @staticmethod
    def store_user_request(db: Session, user_id: str, query: str, result: dict) -> Optional[UserRequest]:
        """Store user request in database."""
        try:
            # Check for duplicate within 15 minutes
            fifteen_minutes_ago = datetime.now(UTC) - timedelta(minutes=15)
            recent_request = db.query(UserRequest).filter(
                UserRequest.user_id == user_id,
                UserRequest.query == query,
                UserRequest.timestamp >= fifteen_minutes_ago
            ).first()
            
            if recent_request:
                logger.info("Duplicate query within 15 minutes, not storing")
                return None
            
            # Ensure user exists
            user = DatabaseService.get_or_create_user(db, user_id)
            
            # Store new request
            request = UserRequest(
                user_id=user_id,
                query=query,
                result=json.dumps(result),
                timestamp=datetime.now(UTC)
            )
            db.add(request)
            db.commit()
            db.refresh(request)
            
            logger.info(f"Stored user request in database: {request.id}")
            return request
            
        except Exception as e:
            logger.error(f"Error storing user request: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_user_history(db: Session, user_id: str, limit: int = 10) -> UserHistoryResponse:
        """Get user's request history from database."""
        try:
            # Ensure user exists
            user = DatabaseService.get_or_create_user(db, user_id)
            
            # Get recent requests
            requests = db.query(UserRequest).filter(
                UserRequest.user_id == user_id
            ).order_by(desc(UserRequest.timestamp)).limit(limit).all()
            
            # Get total count
            total_requests = db.query(UserRequest).filter(
                UserRequest.user_id == user_id
            ).count()
            
            # Convert to response format
            requests_history = []
            for req in requests:
                try:
                    result = json.loads(req.result)
                    requests_history.append(RequestHistoryItem(
                        query=req.query,
                        result=result,
                        timestamp=req.timestamp.isoformat(),
                        request_id=str(req.id)
                    ))
                except Exception as e:
                    logger.error(f"Error parsing request result: {e}")
                    continue
            
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=total_requests,
                recent_requests=requests_history,
                message="Welcome to your request history!"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving user history: {e}")
            return UserHistoryResponse(
                user_id=user_id,
                total_requests=0,
                recent_requests=[],
                message="Welcome! No request history yet."
            )
    
    @staticmethod
    def cleanup_old_requests(db: Session, days: int = 30) -> int:
        """Clean up old requests older than specified days."""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days)
            deleted = db.query(UserRequest).filter(
                UserRequest.timestamp < cutoff_date
            ).delete()
            db.commit()
            logger.info(f"Cleaned up {deleted} old requests")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old requests: {e}")
            db.rollback()
            return 0 