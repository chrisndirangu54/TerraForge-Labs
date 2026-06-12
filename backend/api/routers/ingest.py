from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.auth.projects import (
    ensure_project_access,
    ensure_projects_access,
    get_accessible_project_ids,
)
from backend.api.services.field_data_catalog import (
    catalog_field_datasets,
    register_field_upload,
)
from backend.api.services.ingest import ingest_observations, list_project_observations
from backend.api.services.response_display import enrich_response
from shared.schemas.observation import ObservationRecord

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/field-catalog")
async def field_catalog(user: dict = Depends(get_current_user)) -> dict:
    _ = user
    return enrich_response(catalog_field_datasets())


@router.post("/field-upload/register")
async def field_upload_register(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    _ = user
    dataset = payload.get("dataset")
    files = payload.get("files")
    if not dataset or not isinstance(files, list) or not files:
        raise HTTPException(status_code=400, detail="dataset and files are required")
    return enrich_response(
        register_field_upload(
            dataset=str(dataset),
            files=[str(path) for path in files],
            project_id=payload.get("project_id"),
        )
    )


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