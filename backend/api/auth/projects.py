from __future__ import annotations

from fastapi import HTTPException, status

from backend.api.auth.repository import get_auth_repository
from backend.api.auth.settings import is_auth_required


def get_accessible_project_ids(user: dict) -> set[str] | None:
    """Return project IDs the user may access, or None for unrestricted access."""
    if user.get("id") == "anonymous" or user.get("role") == "admin":
        return None
    projects = get_auth_repository().list_projects(user_id=user["id"])
    return {project["id"] for project in projects}


def user_has_project_access(user: dict, project_id: str) -> bool:
    allowed = get_accessible_project_ids(user)
    if allowed is None:
        return True
    return project_id in allowed


def ensure_project_access(user: dict, project_id: str | None) -> None:
    if not project_id:
        return
    if not user_has_project_access(user, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )


def ensure_projects_access(user: dict, project_ids: set[str]) -> None:
    for project_id in project_ids:
        ensure_project_access(user, project_id)


def require_project_id_when_authenticated(user: dict, project_id: str | None) -> str:
    if project_id:
        ensure_project_access(user, project_id)
        return project_id
    if is_auth_required() and user.get("id") != "anonymous":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id is required",
        )
    return project_id or ""