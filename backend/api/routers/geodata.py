from __future__ import annotations

from fastapi import APIRouter

from backend.api.kriging import run_kriging_pipeline
from shared.constants import KRIGING_GRID_RESOLUTION, KRIGING_MAX_POINTS, VARIOGRAM_MODEL
from fastapi import APIRouter
from pydantic import BaseModel

from shared.constants import KRIGING_MAX_POINTS, VARIOGRAM_MODEL

router = APIRouter()


@router.post("/fuse-geodata")
async def fuse_geodata(payload: dict) -> dict:
    payload.setdefault("grid_resolution_m", KRIGING_GRID_RESOLUTION)
    payload.setdefault("max_points", KRIGING_MAX_POINTS)
    payload.setdefault("variogram_model", VARIOGRAM_MODEL)
    return run_kriging_pipeline(payload)
class GeodataInput(BaseModel):
    observations: list[dict]


@router.post("/fuse-geodata")
async def fuse_geodata(payload: GeodataInput) -> dict:
    return {
        "mode": "phase0-stub",
        "variogram_model": VARIOGRAM_MODEL,
        "kriging_max_points": KRIGING_MAX_POINTS,
        "observation_count": len(payload.observations),
        "grid": [[0.0, 0.1], [0.2, 0.3]],
        "variance": [[0.01, 0.02], [0.03, 0.04]],
    }
