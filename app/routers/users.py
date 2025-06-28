"""
Users router for handling user-related endpoints.
"""

from fastapi import APIRouter, Depends

from ..dependencies import get_user_id
from core.services.user_service import UserService
from core.models.requests import UserHistoryResponse

router = APIRouter(prefix="/api/history", tags=["users"])

@router.get("/", response_model=UserHistoryResponse)
async def get_user_history(
    user_id: str = Depends(get_user_id)
):
    """
    Home page that shows user's request history.
    """
    return await UserService.get_user_history(user_id) 