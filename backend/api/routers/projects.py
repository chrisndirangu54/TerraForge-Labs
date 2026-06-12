from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth.dependencies import get_current_user, require_roles
from backend.api.auth.models import MembershipRequest, ProjectCreateRequest, ProjectResponse
from backend.api.auth.repository import get_auth_repository

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: dict = Depends(get_current_user)) -> list[ProjectResponse]:
    repo = get_auth_repository()
    user_id = None if user["id"] == "anonymous" else user["id"]
    projects = repo.list_projects(user_id=user_id)
    return [ProjectResponse(**project) for project in projects]


@router.post("", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreateRequest,
    user: dict = Depends(require_roles("admin", "geologist")),
) -> ProjectResponse:
    if user["id"] == "anonymous":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create projects",
        )
    repo = get_auth_repository()
    project = repo.create_project(payload.slug, payload.name, user["id"])
    return ProjectResponse(**project)


@router.get("/{project_id}/members")
async def list_project_members(
    project_id: str,
    _: dict = Depends(require_roles("admin", "geologist")),
) -> list[dict]:
    repo = get_auth_repository()
    return repo.list_memberships(project_id)


@router.post("/{project_id}/members")
async def add_project_member(
    project_id: str,
    payload: MembershipRequest,
    _: dict = Depends(require_roles("admin")),
) -> dict:
    repo = get_auth_repository()
    try:
        return repo.add_membership(project_id, payload.user_id, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc