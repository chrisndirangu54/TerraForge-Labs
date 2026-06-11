from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.api.services.storage import get_storage_service

_STAC_ITEMS: dict[str, dict[str, Any]] = {}


def _build_stac_item(
    *,
    asset_key: str,
    bbox: list[float],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    item_id = str(uuid4())
    storage = get_storage_service()
    return {
        "id": item_id,
        "type": "Feature",
        "stac_version": "1.0.0",
        "collection": metadata.get("collection", "terraforge-rasters"),
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]
            ],
        },
        "bbox": bbox,
        "properties": {
            "datetime": metadata.get(
                "datetime", datetime.now(timezone.utc).isoformat()
            ),
            "proj:epsg": metadata.get("epsg", 4326),
            "processing:level": metadata.get("processing_level", "L2A"),
            "terraforge:source": metadata.get("source", "synthetic"),
        },
        "assets": {
            "data": {
                "href": storage.get_public_url(asset_key),
                "type": metadata.get("content_type", "image/tiff"),
                "roles": ["data"],
            },
            "tiles": {
                "href": storage.get_signed_url(
                    f"tiles/{item_id}/{{z}}/{{x}}/{{y}}.png"
                ),
                "type": "image/png",
                "roles": ["tiles"],
            },
        },
        "links": [
            {
                "rel": "self",
                "href": storage.get_signed_url(f"stac/items/{item_id}.json"),
            }
        ],
    }


def ingest_raster(payload: dict[str, Any]) -> dict[str, Any]:
    """Ingest raster bytes/metadata, persist artifact, and register a STAC item."""

    storage = get_storage_service()
    bbox = [float(value) for value in payload.get("bbox", [37.45, -1.20, 37.55, -1.10])]
    raster_bytes = payload.get("raster_bytes")
    if raster_bytes is None:
        width = int(payload.get("width", 64))
        height = int(payload.get("height", 64))
        raster_bytes = _synthetic_raster_bytes(
            width, height, seed=int(payload.get("seed", 42))
        )
    elif isinstance(raster_bytes, str):
        raster_bytes = raster_bytes.encode("utf-8")

    asset_key = payload.get("asset_key") or f"rasters/{uuid4().hex}.tif"
    artifact = storage.put(
        asset_key,
        raster_bytes,
        content_type="image/tiff",
        metadata={
            "bbox": bbox,
            "source": payload.get("source", "synthetic"),
        },
    )

    stac_item = _build_stac_item(
        asset_key=asset_key,
        bbox=bbox,
        metadata={
            "collection": payload.get("collection", "terraforge-rasters"),
            "source": payload.get("source", "synthetic"),
            "epsg": payload.get("epsg", 4326),
            "processing_level": payload.get("processing_level", "L2A"),
            "content_type": "image/tiff",
        },
    )
    stac_key = f"stac/items/{stac_item['id']}.json"
    storage.put(
        stac_key, json.dumps(stac_item, indent=2), content_type="application/json"
    )
    _STAC_ITEMS[stac_item["id"]] = stac_item

    tile_template = storage.get_signed_url("tiles/{z}/{x}/{y}.png")
    return {
        "stac_item_id": stac_item["id"],
        "artifact_id": artifact["id"],
        "artifact_key": asset_key,
        "artifact_url": storage.get_public_url(asset_key),
        "stac_url": storage.get_public_url(stac_key),
        "tile_redirect_template": tile_template,
        "bbox": bbox,
    }


def get_stac_item(item_id: str) -> dict[str, Any] | None:
    return _STAC_ITEMS.get(item_id)


def list_stac_items() -> list[dict[str, Any]]:
    return list(_STAC_ITEMS.values())


def _synthetic_raster_bytes(width: int, height: int, *, seed: int) -> bytes:
    import numpy as np

    rng = np.random.default_rng(seed)
    grid = rng.random((height, width))
    lines = [",".join(f"{value:.4f}" for value in row) for row in grid]
    return ("\n".join(lines)).encode("utf-8")


def reset_raster_pipeline() -> None:
    _STAC_ITEMS.clear()
