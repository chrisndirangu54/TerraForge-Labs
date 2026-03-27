from fastapi import APIRouter
from pydantic import BaseModel

from shared.constants import KRIGING_MAX_POINTS, VARIOGRAM_MODEL

router = APIRouter()


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
