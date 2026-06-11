from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.api.jobs.store import get_job_store

router = APIRouter()


@router.get("/jobs")
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
    job_type: str | None = None,
) -> dict:
    store = get_job_store()
    items = store.list_jobs(
        limit=limit, offset=offset, status=status, job_type=job_type
    )
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    store = get_job_store()
    item = store.get(job_id)
    return {"job_id": job_id, **item}


@router.get("/jobs/{job_id}/events")
async def get_job_events(job_id: str) -> dict:
    store = get_job_store()
    if store.get(job_id).get("status") == "pending" and not store.get_events(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "events": store.get_events(job_id)}
