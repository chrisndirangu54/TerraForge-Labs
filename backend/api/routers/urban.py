from __future__ import annotations

from fastapi import APIRouter

from backend.processing.urban_analysis import (
    classify_settlement,
    estimate_population,
    mining_settlement_conflict,
    service_access,
    suitability_score,
)

router = APIRouter()


@router.post("/urban/classify-settlement")
async def classify_settlement_endpoint(payload: dict) -> dict:
    return classify_settlement(payload)


@router.post("/urban/service-access")
async def service_access_endpoint(payload: dict) -> dict:
    return service_access(
        float(payload.get("distance_km", 2.5)),
        payload.get("service_type", "water_point"),
    )


@router.post("/urban/suitability")
async def suitability_endpoint(payload: dict) -> dict:
    return suitability_score(payload)


@router.post("/urban/conflict-check")
async def conflict_endpoint(payload: dict) -> dict:
    return mining_settlement_conflict(float(payload.get("distance_m", 500)))


@router.get("/urban/settlements")
async def settlements(bbox: str = "") -> dict:
    return {"bbox": bbox, "settlements_url": "minio://urban/settlements.geojson"}


@router.get("/urban/land-use")
async def land_use(bbox: str = "") -> dict:
    return {"bbox": bbox, "worldcover_url": "minio://urban/esa_worldcover.tif"}


@router.get("/urban/population")
async def population(bbox: str = "", building_count: int = 100) -> dict:
    return {"bbox": bbox, **estimate_population(building_count)}
