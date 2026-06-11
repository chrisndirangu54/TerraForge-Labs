from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.auth.projects import (
    ensure_project_access,
    ensure_projects_access,
    get_accessible_project_ids,
)
from backend.api.services.ingest import ingest_observations, list_project_observations
from shared.schemas.observation import ObservationRecord

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/observations")
async def ingest_observation_batch(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    observations_raw = payload.get("observations")
    if not isinstance(observations_raw, list) or not observations_raw:
        raise HTTPException(
            status_code=400, detail="observations must be a non-empty list"
        )

    try:
        observations = [ObservationRecord(**item) for item in observations_raw]
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    project_ids = {obs.project_id for obs in observations}
    ensure_projects_access(user, project_ids)
    return ingest_observations(observations)


@router.get("/observations")
async def get_observations(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
) -> dict:
    allowed = get_accessible_project_ids(user)
    if project_id:
        ensure_project_access(user, project_id)
        return list_project_observations(
            project_id=project_id, limit=limit, offset=offset
        )

    project_ids = None if allowed is None else sorted(allowed)
    return list_project_observations(
        project_ids=project_ids, limit=limit, offset=offset
    )
