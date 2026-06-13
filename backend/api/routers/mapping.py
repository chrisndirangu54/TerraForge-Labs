from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, Response

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.services.storage import get_storage_service
from backend.processing.raster_pipeline import (
    get_stac_item,
    ingest_raster,
    list_stac_items,
)
from backend.api.services.response_display import enrich_response
from backend.processing.cog_tiles import cog_metadata, cog_preview, cog_tile_response
from backend.api.services.map_layers import build_map_layers_response
from backend.processing.mapping_stack import (
    cesium_tileset_job,
    map_provider_plan,
    offline_pack_manifest,
)

router = APIRouter()


@router.get("/tiles/{z}/{x}/{y}")
async def vector_tile(z: int, x: int, y: int) -> RedirectResponse:
    storage = get_storage_service()
    tile_key = f"tiles/{z}/{x}/{y}.mvt"
    if not storage.exists(tile_key):
        storage.put(
            tile_key,
            f"MVT placeholder {z}/{x}/{y}",
            content_type="application/vnd.mapbox-vector-tile",
        )
    return RedirectResponse(url=storage.get_signed_url(tile_key), status_code=302)


@router.get("/tiles/raster/{z}/{x}/{y}")
async def raster_tile(z: int, x: int, y: int) -> RedirectResponse:
    storage = get_storage_service()
    tile_key = f"tiles/raster/{z}/{x}/{y}.png"
    if not storage.exists(tile_key):
        storage.put(tile_key, b"PNG-PLACEHOLDER", content_type="image/png")
    return RedirectResponse(url=storage.get_signed_url(tile_key), status_code=302)


@router.get("/tiles/offline/{region}")
async def offline_tiles(region: str, include_satellite: bool = True) -> dict:
    return enrich_response(offline_pack_manifest(region, include_satellite))


@router.get("/basemap/sentinel2")
async def sentinel2_basemap(bbox: str = "", date: str = "latest") -> dict:
    storage = get_storage_service()
    return {
        "bbox": bbox,
        "date": date,
        "tile_url": storage.get_signed_url("basemaps/sentinel2/{z}/{x}/{y}.png"),
    }


@router.post("/mapping/rasters/ingest", dependencies=[Depends(require_mutating_access)])
async def ingest_raster_asset(payload: dict) -> dict:
    return ingest_raster(payload)


@router.get("/mapping/stac/items")
async def query_stac_items(
    collection: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _: dict = Depends(get_current_user),
) -> dict:
    items = list_stac_items(collection=collection, project_id=project_id, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/mapping/stac/items/{item_id}")
async def fetch_stac_item(
    item_id: str,
    _: dict = Depends(get_current_user),
) -> dict:
    item = get_stac_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="STAC item not found")
    return item


@router.get("/mapping/layers")
async def mapping_layers(
    project_id: str | None = Query(default=None),
) -> dict:
    return enrich_response(build_map_layers_response(project_id=project_id))


@router.get("/mapping/cog/{storage_key:path}/metadata")
async def mapping_cog_metadata(storage_key: str) -> dict:
    try:
        return cog_metadata(storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/mapping/cog/{storage_key:path}/preview.png")
async def mapping_cog_preview(storage_key: str) -> Response:
    try:
        content, media_type = cog_preview(storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=content, media_type=media_type)


@router.get("/mapping/cog/{storage_key:path}/tiles/{z}/{x}/{y}.png")
async def mapping_cog_tile(storage_key: str, z: int, x: int, y: int) -> Response:
    try:
        content, media_type = cog_tile_response(storage_key, z=z, x=x, y=y)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=content, media_type=media_type)


@router.get("/mapping/provider-plan")
async def provider_plan(use_google: bool = False) -> dict:
    return map_provider_plan(use_google)


@router.post("/mapping/cesium-tileset", dependencies=[Depends(require_mutating_access)])
async def cesium_tileset(payload: dict) -> dict:
    return cesium_tileset_job(
        payload.get("job_id", "matuu"),
        payload.get("source_obj_url", "minio://models/matuu.obj"),
    )
