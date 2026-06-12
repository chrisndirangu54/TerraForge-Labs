from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth.dependencies import get_current_user
from backend.api.auth.projects import ensure_project_access, get_accessible_project_ids
from backend.api.jobs.store import get_job_store

router = APIRouter()


def _project_filter(user: dict) -> list[str] | None:
    allowed = get_accessible_project_ids(user)
    if allowed is None:
        return None
    return sorted(allowed)


def _ensure_job_visible(user: dict, job: dict) -> None:
    project_id = job.get("project_id")
    if not project_id:
        return
    ensure_project_access(user, str(project_id))


@router.get("/jobs")
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
    job_type: str | None = None,
    project_id: str | None = None,
    user: dict = Depends(get_current_user),
) -> dict:
    if project_id:
        ensure_project_access(user, project_id)
        project_ids = [project_id]
    else:
        project_ids = _project_filter(user)

    store = get_job_store()
    items = store.list_jobs(
        limit=limit,
        offset=offset,
        status=status,
        job_type=job_type,
        project_ids=project_ids,
    )
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    store = get_job_store()
    item = store.get(job_id)
    if item.get("status") == "pending":
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_visible(user, item)
    return {"job_id": job_id, **item}


@router.get("/jobs/{job_id}/events")
async def get_job_events(
    job_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    store = get_job_store()
    item = store.get(job_id)
    if item.get("status") == "pending" and not store.get_events(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_visible(user, item)
    return {"job_id": job_id, "events": store.get_events(job_id)}