from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access

from backend.api.services.response_display import enrich_response
from backend.processing.urban_analysis import (
    classify_settlement,
    estimate_population,
    mining_settlement_conflict,
    service_access,
    suitability_score,
)

router = APIRouter()


@router.post(
    "/urban/classify-settlement", dependencies=[Depends(require_mutating_access)]
)
async def classify_settlement_endpoint(payload: dict) -> dict:
    return classify_settlement(payload)


@router.post("/urban/service-access", dependencies=[Depends(require_mutating_access)])
async def service_access_endpoint(payload: dict) -> dict:
    return service_access(
        float(payload.get("distance_km", 2.5)),
        payload.get("service_type", "water_point"),
    )


@router.post("/urban/suitability", dependencies=[Depends(require_mutating_access)])
async def suitability_endpoint(payload: dict) -> dict:
    return suitability_score(payload)


@router.post("/urban/conflict-check", dependencies=[Depends(require_mutating_access)])
async def conflict_endpoint(payload: dict) -> dict:
    return mining_settlement_conflict(float(payload.get("distance_m", 500)))


@router.get("/urban/settlements")
async def settlements(bbox: str = "") -> dict:
    return enrich_response(
        {
            "bbox": bbox,
            "settlements_url": "minio://urban/settlements.geojson",
            "settlements": [
                {"id": "SET-MAT-01", "name": "Matuu Township", "lon": 37.48, "lat": -1.15, "buildings": 420, "class": "market_town"},
                {"id": "SET-MAT-02", "name": "Kithimani", "lon": 37.52, "lat": -1.12, "buildings": 180, "class": "rural_cluster"},
                {"id": "SET-MAT-03", "name": "Ikombe", "lon": 37.45, "lat": -1.18, "buildings": 95, "class": "farmstead"},
            ],
        }
    )


@router.get("/urban/land-use")
async def land_use(bbox: str = "") -> dict:
    return {"bbox": bbox, "worldcover_url": "minio://urban/esa_worldcover.tif"}


@router.get("/urban/population")
async def population(bbox: str = "", building_count: int = 100) -> dict:
    return {"bbox": bbox, **estimate_population(building_count)}
