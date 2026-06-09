from __future__ import annotations

from fastapi import APIRouter

from backend.api.kriging import run_kriging_pipeline
from shared.constants import KRIGING_GRID_RESOLUTION, KRIGING_MAX_POINTS, VARIOGRAM_MODEL

router = APIRouter()


@router.post("/fuse-geodata")
async def fuse_geodata(payload: dict) -> dict:
    payload.setdefault("grid_resolution_m", KRIGING_GRID_RESOLUTION)
    payload.setdefault("max_points", KRIGING_MAX_POINTS)
    payload.setdefault("variogram_model", VARIOGRAM_MODEL)
    return run_kriging_pipeline(payload)
