"""
FastAPI dependencies for dependency injection.
"""

from fastapi import Request, Response

from .services.user_service import UserService


async def get_user_id(request: Request, response: Response) -> str:
    """FastAPI dependency to get or create user ID."""
    return UserService.get_or_create_user_id(request, response) 