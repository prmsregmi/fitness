"""
Admin router for handling system and cache management endpoints.
"""

from fastapi import APIRouter

from ..cache import request_cache
from ..models.requests import HealthResponse, CacheClearResponse

router = APIRouter(tags=["admin"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API status.
    """
    return HealthResponse(status="healthy")


@router.get("/cache/clear", response_model=CacheClearResponse)
async def clear_cache():
    """
    Clear the entire response cache.
    """
    await request_cache.clear()
    return CacheClearResponse(message="Cache cleared successfully") 