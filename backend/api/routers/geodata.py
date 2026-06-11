from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.kriging import run_kriging_pipeline
from backend.api.tasks import celery_run_kriging, run_kriging
from shared.constants import (
    KRIGING_GRID_RESOLUTION,
    KRIGING_MAX_POINTS,
    VARIOGRAM_MODEL,
)

router = APIRouter()


@router.post("/fuse-geodata")
async def fuse_geodata(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    payload.setdefault("grid_resolution_m", KRIGING_GRID_RESOLUTION)
    payload.setdefault("max_points", KRIGING_MAX_POINTS)
    payload.setdefault("variogram_model", VARIOGRAM_MODEL)
    return submit_job(
        job_type="kriging",
        payload=payload,
        runner=run_kriging,
        celery_task=celery_run_kriging,
        async_default=True,
        meta={"pipeline": run_kriging_pipeline.__name__},
    )
