from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.auth.dependencies import get_current_user
from backend.api.services.exploration_summary import build_exploration_summary

router = APIRouter()


@router.get("/projects/exploration-summary")
async def exploration_summary(
    project_id: str | None = Query(default=None),
    commodity: str = Query(default="ta"),
    _: dict = Depends(get_current_user),
) -> dict:
    return build_exploration_summary(project_id=project_id, commodity=commodity)