from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.api.services.stac_catalog import get_stac_catalog
from backend.api.services.storage import get_storage_service


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
            "terraforge:project_id": metadata.get("project_id"),
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
    catalog = get_stac_catalog()
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
            "project_id": payload.get("project_id"),
        },
    )

    catalog.register_artifact(
        {
            "id": artifact["id"],
            "project_id": payload.get("project_id"),
            "artifact_type": "raster",
            "storage_key": asset_key,
            "content_type": "image/tiff",
            "size_bytes": artifact["size_bytes"],
            "checksum": artifact["checksum"],
            "metadata": artifact.get("metadata", {}),
        }
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
            "project_id": payload.get("project_id"),
        },
    )
    stac_key = f"stac/items/{stac_item['id']}.json"
    storage.put(
        stac_key, json.dumps(stac_item, indent=2), content_type="application/json"
    )
    catalog.register_stac_item(
        item=stac_item,
        artifact_id=artifact["id"],
        project_id=payload.get("project_id"),
    )

    tile_template = storage.get_signed_url("tiles/{z}/{x}/{y}.png")
    return {
        "stac_item_id": stac_item["id"],
        "artifact_id": artifact["id"],
        "artifact_key": asset_key,
        "artifact_url": storage.get_public_url(asset_key),
        "artifact_signed_url": storage.get_signed_url(asset_key),
        "stac_url": storage.get_public_url(stac_key),
        "stac_signed_url": storage.get_signed_url(stac_key),
        "tile_redirect_template": tile_template,
        "bbox": bbox,
        "storage_backend": storage.backend,
    }


def get_stac_item(item_id: str) -> dict[str, Any] | None:
    catalog = get_stac_catalog()
    row = catalog.get_stac_item(item_id)
    if row is None:
        return None
    storage = get_storage_service()
    stac_key = f"stac/items/{item_id}.json"
    return {
        **row,
        "item_id": row.get("item_id", item_id),
        "stac_signed_url": storage.get_signed_url(stac_key),
    }


def list_stac_items(
    *,
    collection: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return get_stac_catalog().list_stac_items(
        collection=collection, project_id=project_id, limit=limit
    )


def _synthetic_raster_bytes(width: int, height: int, *, seed: int) -> bytes:
    import numpy as np

    rng = np.random.default_rng(seed)
    grid = rng.random((height, width))
    lines = [",".join(f"{value:.4f}" for value in row) for row in grid]
    return ("\n".join(lines)).encode("utf-8")


def reset_raster_pipeline() -> None:
    from backend.api.services.stac_catalog import reset_stac_catalog

    reset_stac_catalog()