"""
Fitness API main application module.

This module provides the main FastAPI application instance and configuration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from .routers import users, search, admin as admin_router
from .admin import UserAdmin, TaskAdmin, SearchRequestAdmin

from core.models.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fitness API",
    description="A fitness application with search and user tracking capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up admin interface
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)
admin.add_view(SearchRequestAdmin)

# Include routers
app.include_router(users.router)
app.include_router(search.router)
app.include_router(admin_router.router)