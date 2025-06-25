"""
Users router for handling user-related endpoints.
"""

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_user_id
from ..services.user_service import UserService
from ..models.requests import UserHistoryResponse

router = APIRouter(tags=["users"])


@router.get("/", response_model=UserHistoryResponse)
async def get_user_history(
    user_id: str = Depends(get_user_id),
    load_old: bool = Query(
        default=False,
        description="Load old data from database in addition to Redis cache"
    )
):
    """
    Home page that shows user's request history.
    When load_old=False (default), shows only recent data from Redis cache.
    When load_old=True, also loads historical data from SQLite database.
    """
    return await UserService.get_user_history(user_id, load_old=load_old) 