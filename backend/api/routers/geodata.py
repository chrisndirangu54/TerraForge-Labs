from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.services.kriging_observations import (
    extract_kriging_points,
    resolve_kriging_observations,
)
from backend.api.services.response_display import enrich_response
from backend.api.tasks import celery_run_kriging, run_kriging
from backend.processing.variogram_cv import analyze_variogram
from shared.constants import (
    KRIGING_GRID_RESOLUTION,
    KRIGING_MAX_POINTS,
    VARIOGRAM_MODEL,
)

router = APIRouter()


@router.post("/geodata/variogram/cross-validate")
async def variogram_cross_validate(payload: dict) -> dict:
    observations = resolve_kriging_observations(payload)
    element = payload.get("element", "ta_ppm")
    if len(observations) < 4:
        return enrich_response(
            {
                "error": "insufficient_points",
                "count": len(observations),
                "element": element,
            }
        )
    xs, ys, values = extract_kriging_points(observations, element=element)
    if len(values) < 4:
        return enrich_response(
            {
                "error": "insufficient_points",
                "count": len(values),
                "element": element,
            }
        )
    return enrich_response(
        analyze_variogram(
            xs,
            ys,
            values,
            variogram_model=str(payload.get("variogram_model", "spherical")),
        )
    )


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
    )