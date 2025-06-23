"""
Database models for persistent storage of user requests and history.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, create_engine
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
    
    # Relationship to requests
    requests = relationship("UserRequest", back_populates="user", cascade="all, delete-orphan")


class UserRequest(Base):
    """User request model for storing search history."""
    __tablename__ = "user_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    result = Column(Text, nullable=False)  # JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship to user
    user = relationship("User", back_populates="requests")


class SearchCache(Base):
    """Search cache model for caching API results."""
    __tablename__ = "search_cache"
    
    id = Column(String, primary_key=True)  # query hash or query string
    query = Column(Text, nullable=False)
    result = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)


# Database configuration
DATABASE_URL = "sqlite:///./fitness.db"  # Change to PostgreSQL in production
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine) 