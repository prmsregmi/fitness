"""
Pydantic models for request and response data structures.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=5, description="Search query cannot be shorter than 10 characters.")
    force_refresh: Optional[bool] = False
    user_id: Optional[str] = None

    @field_validator('query')
    @classmethod
    def validate_query_not_empty(cls, v):
        if not v or v.strip() == "" or len(v.strip()) < 5:
            raise ValueError("Query cannot be shorter than 10 characters.")
        return v.strip()


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
    load_old: bool = False  # Whether to load old data from database


class HealthResponse(BaseModel):
    status: str


class CacheClearResponse(BaseModel):
    message: str 