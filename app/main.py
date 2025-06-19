"""
Fitness API main application module.

This module provides the main FastAPI application instance and routes
for the fitness application.
"""

import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from core.examples.future_house import future_house_api
from .cache import request_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fitness API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root(
    query: str = Query(
        default="Can human run as fast as the Cheetah",
        description="Query to send to FutureHouse API"
    ),
    force_refresh: bool = Query(
        default=False,
        description="Force a fresh request instead of using cached response"
    )
):
    """
    Root endpoint that provides a welcome message.

    Args:
        query: The query to send to FutureHouse API
        force_refresh: Whether to force a fresh request instead of using cache

    Returns:
        dict: A welcome message dictionary
    """
    try:
        logger.info(f"Processing root endpoint request with query: {query}")
        
        # If force refresh, invalidate the cache for this query
        if force_refresh:
            request_cache.invalidate(query)
        
        # Use the cache to handle the request
        result = await request_cache.get_or_set(
            query,
            lambda: future_house_api(query)
        )
        
        logger.info("Successfully processed FutureHouse API request")
        return {"message": result}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API status.

    Returns:
        dict: The health status of the API
    """
    return {"status": "healthy"}

@app.post("/cache/clear")
async def clear_cache():
    """
    Clear the entire response cache.

    Returns:
        dict: Success message
    """
    request_cache.clear()
    return {"message": "Cache cleared successfully"}