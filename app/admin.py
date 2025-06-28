"""
Admin interface configuration using SQLAdmin.
"""

from sqladmin import ModelView
from core.models.database import User, SearchRequest, Task


class UserAdmin(ModelView, model=User):
    """Admin interface for User model."""
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.created_at, User.last_active]
    column_searchable_list = [User.id]
    column_sortable_list = [User.created_at, User.last_active]
    can_create = False  # Users are created through the API
    can_edit = False   # Users are managed through the API
    can_delete = True  # Allow deletion for cleanup


class TaskAdmin(ModelView, model=Task):
    """Admin interface for Task model."""
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-tasks"
    column_list = [Task.id, Task.user_id, Task.created_at]
    column_searchable_list = [Task.user_id]
    column_sortable_list = [Task.created_at]
    can_create = False  # Tasks are created through the API
    can_edit = False   # Tasks are managed through the API
    can_delete = True  # Allow deletion for cleanup


class SearchRequestAdmin(ModelView, model=SearchRequest):
    """Admin interface for SearchRequest model."""
    name = "Search Request"
    name_plural = "Search Requests"
    icon = "fa-solid fa-search"
    column_list = [
        SearchRequest.id,
        SearchRequest.task_id,
        SearchRequest.query,
        SearchRequest.status,
        SearchRequest.created_at,
        SearchRequest.completed_at
    ]
    column_searchable_list = [SearchRequest.query, SearchRequest.task_id, SearchRequest.id]
    column_sortable_list = [SearchRequest.created_at, SearchRequest.completed_at]
    can_create = False  # Requests are created through the API
    can_edit = False   # Requests are immutable
    can_delete = True  # Allow deletion for cleanup

    # Format the result JSON for better display
    column_formatters = {
        SearchRequest.result: lambda m, a: m.result[:100] + "..." if len(m.result) > 100 else m.result
    }