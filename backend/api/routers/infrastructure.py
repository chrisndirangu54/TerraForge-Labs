from __future__ import annotations

from fastapi import APIRouter

from backend.processing.infrastructure import (
    mining_infrastructure_assessment,
    pipeline_route,
    power_grid_proximity,
    route_assessment,
    telecoms_coverage,
)

router = APIRouter()


@router.post("/infra/route")
async def infra_route(payload: dict) -> dict:
    return route_assessment(
        payload.get("origin", [37.48, -1.15]),
        payload.get("destination", [39.66, -4.04]),
        float(payload.get("distance_km", 485)),
    )


@router.post("/infra/pipeline-route")
async def infra_pipeline_route(payload: dict) -> dict:
    return pipeline_route(
        payload.get("source", [37.48, -1.15]),
        payload.get("destination", [37.55, -1.1]),
        float(payload.get("slope_penalty", 1.0)),
    )


@router.post("/infra/mining-assessment")
async def infra_mining_assessment(payload: dict) -> dict:
    return mining_infrastructure_assessment(payload)


@router.get("/infra/roads")
async def infra_roads(bbox: str = "") -> dict:
    return {"bbox": bbox, "roads_url": "minio://infrastructure/osm_roads.geojson"}


@router.get("/infra/power-grid")
async def infra_power_grid(bbox: str = "", distance_km: float = 12.0) -> dict:
    return {
        "bbox": bbox,
        **power_grid_proximity(distance_km),
        "grid_url": "minio://infrastructure/power_grid.geojson",
    }


@router.get("/infra/telecoms")
async def infra_telecoms(
    bbox: str = "", lat: float = -1.15, nearest_tower_km: float = 22.1
) -> dict:
    return {
        "bbox": bbox,
        **telecoms_coverage(lat, nearest_tower_km),
        "towers_url": "minio://infrastructure/telecoms.geojson",
    }
