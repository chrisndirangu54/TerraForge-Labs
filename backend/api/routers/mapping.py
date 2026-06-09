from __future__ import annotations

from fastapi import APIRouter

from backend.processing.mapping_stack import (
    cesium_tileset_job,
    layer_catalogue,
    map_provider_plan,
    offline_pack_manifest,
)

router = APIRouter()


@router.get("/tiles/{z}/{x}/{y}")
async def vector_tile(z: int, x: int, y: int) -> dict:
    return {
        "z": z,
        "x": x,
        "y": y,
        "tile_url": f"martin://geological/{z}/{x}/{y}.mvt",
        "target_ms": 100,
    }


@router.get("/tiles/offline/{region}")
async def offline_tiles(region: str, include_satellite: bool = True) -> dict:
    return offline_pack_manifest(region, include_satellite)


@router.get("/basemap/sentinel2")
async def sentinel2_basemap(bbox: str = "", date: str = "latest") -> dict:
    return {
        "bbox": bbox,
        "date": date,
        "tile_url": "minio://basemaps/sentinel2/{z}/{x}/{y}.png",
    }


@router.get("/mapping/layers")
async def mapping_layers() -> dict:
    return layer_catalogue()


@router.get("/mapping/provider-plan")
async def provider_plan(use_google: bool = False) -> dict:
    return map_provider_plan(use_google)


@router.post("/mapping/cesium-tileset")
async def cesium_tileset(payload: dict) -> dict:
    return cesium_tileset_job(
        payload.get("job_id", "matuu"),
        payload.get("source_obj_url", "minio://models/matuu.obj"),
    )
