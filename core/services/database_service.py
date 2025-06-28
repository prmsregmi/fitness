"""
Database service for handling persistent data operations.
"""

import json
import logging
from datetime import datetime, timedelta, UTC
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.database import SessionLocal, User, SearchRequest, Task
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
    def create_user_and_task(db: Session) -> tuple[User, Task]:
        """Create a new user and task for each search request."""
        try:
            # Create new user
            user = User()
            db.add(user)
            db.flush()  # Flush to get the user ID
            
            # Create new task for this user
            task = Task(user_id=user.id)
            db.add(task)
            db.flush()  # Flush to get the task ID
            
            db.commit()
            db.refresh(user)
            db.refresh(task)
            
            logger.info(f"Created new user {user.id} and task {task.id}")
            return user, task
            
        except Exception as e:
            logger.error(f"Error creating user and task: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def store_search_request(db: Session, query_hash: str, task_id, query: str, result: dict, status: str = "completed") -> Optional[SearchRequest]:
        """Store search request in database with hex hash as ID."""
        try:
            logger.info(f"Attempting to store search request: hash={query_hash}, task_id={task_id}, query={query}")
            
            # Check if this exact search already exists for this task
            existing_request = db.query(SearchRequest).filter(
                SearchRequest.id == query_hash,
                SearchRequest.task_id == task_id
            ).first()
            
            if existing_request:
                logger.info(f"Search request with hash {query_hash} already exists for task {task_id}")
                return existing_request
            
            # Store new request with hex hash as ID
            request = SearchRequest(
                id=query_hash,  # Use the hex hash as ID
                task_id=task_id,
                query=query,
                result=json.dumps(result),
                status=status,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC) if status == "completed" else None
            )
            
            logger.info(f"Created SearchRequest object: {request}")
            db.add(request)
            logger.info("Added SearchRequest to session")
            db.commit()
            logger.info("Committed SearchRequest to database")
            db.refresh(request)
            
            logger.info(f"Successfully stored search request with hash {query_hash} for task {task_id}")
            return request
            
        except Exception as e:
            logger.error(f"Error storing search request: {e}")
            logger.exception("Full exception details:")
            db.rollback()
            return None
    
    @staticmethod
    def get_search_by_hash_and_task(db: Session, query_hash: str, task_id: str) -> Optional[SearchRequest]:
        """Get search request by hash and task ID."""
        try:
            return db.query(SearchRequest).filter(
                SearchRequest.id == query_hash,
                SearchRequest.task_id == task_id
            ).first()
        except Exception as e:
            logger.error(f"Error retrieving search by hash and task: {e}")
            return None
    
    @staticmethod
    def get_search_history(db: Session, limit: int = 10) -> list:
        """Get recent search history from database."""
        try:
            requests = db.query(SearchRequest).order_by(desc(SearchRequest.created_at)).limit(limit).all()
            requests_history = []
            for req in requests:
                try:
                    result = json.loads(req.result)
                    requests_history.append({
                        "query": req.query,
                        "result": result,
                        "timestamp": req.created_at.isoformat(),
                        "request_id": req.id,  # Now this is the hex hash
                        "task_id": str(req.task_id),
                        "status": req.status,
                        "completed_at": req.completed_at.isoformat() if req.completed_at else None
                    })
                except Exception as e:
                    logger.error(f"Error parsing request result: {e}")
                    continue
            return requests_history
        except Exception as e:
            logger.error(f"Error retrieving search history: {e}")
            return []