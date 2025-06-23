"""
Pydantic models for request and response data structures.
"""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    force_refresh: bool = False


class SearchResponse(BaseModel):
    message: Any
    user_id: str
    query: str


class RequestHistoryItem(BaseModel):
    query: str
    result: Optional[Any] = None
    timestamp: str
    request_id: str
    status: Optional[str] = "completed"  # pending, completed, failed
    completed_at: Optional[str] = None


class UserHistoryResponse(BaseModel):
    user_id: str
    total_requests: int
    recent_requests: List[RequestHistoryItem]
    message: str


class HealthResponse(BaseModel):
    status: str


class CacheClearResponse(BaseModel):
    message: str 