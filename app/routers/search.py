"""
Search router for handling search-related endpoints.
"""

from fastapi import APIRouter, HTTPException, Path

from core.services.search_service import SearchService
from core.models.requests import SearchRequest
router = APIRouter(prefix="/api/search", tags=["search"])

@router.post("/")
async def search(search_request: SearchRequest):
    """
    Start an asynchronous search. Returns immediately with task information.
    Use /search/status/{task_id} to check progress.
    """
    try:
        result = await SearchService.start_search(search_request.query, search_request.force_refresh)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Async search start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_search_status(
    task_id: str = Path(..., description="The task ID returned from /search/"),
):
    """
    Get the status of an asynchronous search task.
    """
    try:
        result = await SearchService.get_search_status(task_id)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 