"""
Search router for handling search-related endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Path

from ..dependencies import get_user_id
from ..services.search_service import SearchService
from ..models.requests import SearchRequest

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/")
async def search(
    search_request: SearchRequest,
    system_generated_user_id: str = Depends(get_user_id),
):
    """
    Start an asynchronous search. Returns immediately with task information.
    Use /search/status/{task_id} to check progress.
    """
    user_id = search_request.user_id or system_generated_user_id
    
    try:
        result = await SearchService.start_search(user_id, search_request.query, search_request.force_refresh)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Async search start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_search_status(
    task_id: str = Path(..., description="The task ID returned from /search/async"),
    user_id: str = Depends(get_user_id),
):
    """
    Get the status of an asynchronous search task.
    """
    try:
        result = await SearchService.get_search_status(user_id, task_id)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 