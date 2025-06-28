"""
Database models for persistent storage of user requests and history.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, create_engine, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_active = Column(DateTime, default=lambda: datetime.now(UTC))
    

class Task(Base):
    """Task model for storing task information."""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship to requests
    requests = relationship("SearchRequest", back_populates="task", cascade="all, delete-orphan")

class SearchRequest(Base):
    """Search cache model for caching API results."""
    __tablename__ = "search_requests"
    
    # Use hex hash string as ID (64 character hex string from SHA256)
    id = Column(String(64), nullable=False)  # SHA256 hex hash
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    query = Column(Text, nullable=False)
    result = Column(Text, nullable=False)  # JSON string
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    
    # Composite primary key: (id, task_id)
    __table_args__ = (
        PrimaryKeyConstraint('id', 'task_id'),
    )
    
    # Relationship back to task
    task = relationship("Task", back_populates="requests")


# Database configuration
DATABASE_URL = "sqlite:///./fitness.db"  # Change to PostgreSQL in production
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine) 