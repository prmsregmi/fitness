"""
Search router for handling search-related endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks

from ..dependencies import get_user_id
from ..services.search_service import SearchService
from ..services.user_service import UserService
from ..models.requests import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/", response_model=SearchResponse)
async def search(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    query: str = Query(
        default="",
        description="Query to send to search API"
    ),
    force_refresh: bool = Query(
        default=False,
        description="Force a fresh request instead of using cached response"
    )
):
    """
    Search endpoint that processes queries and tracks user requests.
    """
    if query == "":
        return SearchResponse(
            message="No query provided",
            user_id=user_id,
            query=""
        )
    
    # Store pending request immediately - shows up in history as "pending"
    request_id = await UserService.store_pending_request(user_id, query)
    
    try:
        # Perform the search (this can take as long as needed)
        result = await SearchService.perform_search(query, force_refresh)
        
        # Update the pending request with the actual result
        background_tasks.add_task(
            UserService.update_request_with_result,
            user_id,
            request_id,
            result
        )
        
        return SearchResponse(
            message=result,
            user_id=user_id,
            query=query
        )
    except Exception as e:
        # Update pending request with error
        import logging
        logging.getLogger(__name__).error(f"Search failed: {str(e)}")
        
        error_result = {"error": str(e), "status": "failed"}
        background_tasks.add_task(
            UserService.update_request_with_result,
            user_id,
            request_id,
            error_result
        )
        
        raise HTTPException(status_code=500, detail=str(e)) 