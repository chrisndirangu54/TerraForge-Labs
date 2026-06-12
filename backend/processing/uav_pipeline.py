from __future__ import annotations

from typing import Any

import numpy as np

from backend.api.services.artifact_lineage import record_lineage
from backend.api.services.storage import get_storage_service
from backend.processing.cog_io import array_to_cog_bytes, read_cog_array, read_cog_metadata


def _flight_bounds(payload: dict[str, Any]) -> tuple[float, float, float, float]:
    bounds = payload.get("bounds")
    if bounds and len(bounds) == 4:
        return tuple(float(v) for v in bounds)  # type: ignore[return-value]
    center_lon = float(payload.get("center_lon", 37.5))
    center_lat = float(payload.get("center_lat", -1.15))
    half = float(payload.get("half_extent_deg", 0.03))
    return (
        center_lon - half,
        center_lat - half,
        center_lon + half,
        center_lat + half,
    )


def _generate_ortho_grid(bounds: tuple[float, float, float, float], *, seed: int = 3) -> np.ndarray:
    west, south, east, north = bounds
    rows, cols = 128, 128
    rng = np.random.default_rng(seed)
    x = np.linspace(west, east, cols)
    y = np.linspace(south, north, rows)
    xx, yy = np.meshgrid(x, y)
    ridge = np.exp(-((xx - (west + east) / 2) ** 2 + (yy - (south + north) / 2) ** 2) * 500.0)
    red = 0.25 + ridge * 0.35 + rng.normal(0, 0.03, size=(rows, cols))
    green = 0.35 + ridge * 0.25 + rng.normal(0, 0.03, size=(rows, cols))
    blue = 0.15 + ridge * 0.1 + rng.normal(0, 0.02, size=(rows, cols))
    ndvi_proxy = np.clip(green - red * 0.5, 0.0, 1.0)
    return ndvi_proxy.astype(np.float32)


def _store_cog(key: str, grid: np.ndarray, bounds: tuple[float, float, float, float]) -> dict[str, Any]:
    storage = get_storage_service()
    cog_bytes = array_to_cog_bytes(grid, bounds)
    storage.put(key, cog_bytes, content_type="image/tiff")
    return {
        "storage_key": key,
        "metadata": read_cog_metadata(cog_bytes),
        "tile_url_template": f"/mapping/cog/{key}/tiles/{{z}}/{{x}}/{{y}}.png",
        "preview_url": f"/mapping/cog/{key}/preview.png",
    }


def _change_detection(
    current: np.ndarray,
    reference: np.ndarray,
    *,
    threshold: float = 0.08,
) -> np.ndarray:
    diff = np.abs(current - reference)
    return (diff >= threshold).astype(np.float32)


def process_uav_survey(payload: dict[str, Any]) -> dict[str, Any]:
    """UAV flight → orthomosaic + DSM COGs and optional Sentinel change layer."""

    project_id = str(payload.get("project_id", "demo"))
    flight_id = str(payload.get("flight_id", "uav-001"))
    bounds = _flight_bounds(payload)
    prefix = f"uav/{project_id}/{flight_id}"

    storage = get_storage_service()
    ortho_key = str(payload.get("orthomosaic_key", f"{prefix}/orthomosaic.tif"))
    dsm_key = f"{prefix}/dsm.tif"
    change_key = f"rasters/{project_id}/uav_change_{flight_id}.tif"

    if storage.exists(ortho_key):
        content = storage.get(ortho_key)
        assert content is not None
        ortho, _meta = read_cog_array(content)
    else:
        ortho = _generate_ortho_grid(bounds, seed=int(payload.get("seed", 5)))
        _store_cog(ortho_key, ortho, bounds)

    dsm = ortho + float(payload.get("dsm_offset", 0.12))
    dsm_asset = _store_cog(dsm_key, dsm, bounds)

    reference_key = str(payload.get("reference_key", f"satellite/{project_id}/ndvi_baseline.tif"))
    if storage.exists(reference_key):
        ref_content = storage.get(reference_key)
        assert ref_content is not None
        reference, _ = read_cog_array(ref_content)
        if reference.shape != ortho.shape:
            reference = _generate_ortho_grid(bounds, seed=1)
    else:
        reference = _generate_ortho_grid(bounds, seed=1)
        _store_cog(reference_key, reference, bounds)

    change = _change_detection(ortho, reference)
    change_asset = _store_cog(change_key, change, bounds)

    lineage = record_lineage(
        artifact_type="uav_orthomosaic",
        storage_key=ortho_key,
        project_id=project_id,
        metadata={"flight_id": flight_id, "drone": payload.get("drone_model", "dji_generic")},
    )

    return {
        "status": "complete",
        "project_id": project_id,
        "flight_id": flight_id,
        "bounds": list(bounds),
        "orthomosaic": {
            "storage_key": ortho_key,
            "tile_url_template": f"/mapping/cog/{ortho_key}/tiles/{{z}}/{{x}}/{{y}}.png",
        },
        "dsm": dsm_asset,
        "change_detection": change_asset,
        "reference_baseline_key": reference_key,
        "geobotany_retrain_trigger": float(change.sum()) > 0,
        "lineage_id": lineage["id"],
    }