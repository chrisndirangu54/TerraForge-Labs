from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_lidar_file(
    filepath: str | Path,
    *,
    project_id: str = "capture",
    resolution_m: float = 5.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run LAZ/LAS through the LiDAR pipeline and return a display-friendly row + raster meta."""

    from backend.api.services.storage import get_storage_service
    from backend.processing.lidar_pipeline import process_lidar_to_cogs

    path = Path(filepath)
    if path.suffix.lower() not in {".las", ".laz"}:
        raise ValueError("Expected .las or .laz")

    storage = get_storage_service()
    storage_key = f"lidar/{project_id}/{path.name}"
    if not storage.exists(storage_key):
        storage.put(
            storage_key,
            path.read_bytes(),
            content_type="application/octet-stream",
        )

    result = process_lidar_to_cogs(
        {
            "project_id": project_id,
            "storage_key": storage_key,
            "resolution_m": resolution_m,
        }
    )
    bounds = result.get("bounds") or [37.45, -1.20, 37.55, -1.10]
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2

    row: dict[str, Any] = {
        "sample_id": path.stem,
        "lon": center_lon,
        "lat": center_lat,
        "point_count": result.get("point_count"),
        "reader": result.get("reader"),
        "resolution_m": result.get("resolution_m"),
        "dtm_key": (result.get("dtm") or {}).get("storage_key"),
        "dsm_key": (result.get("dsm") or {}).get("storage_key"),
        "chm_key": (result.get("chm") or {}).get("storage_key"),
        "slope_key": (result.get("slope") or {}).get("storage_key"),
        "flagged": False,
        "pipeline_result": result,
    }

    preview = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [center_lon, center_lat]},
                "properties": {
                    "name": path.stem,
                    "point_count": result.get("point_count"),
                },
            }
        ],
    }
    return [row], {"validation": {"warnings": [], "flagged_count": 0}, "geojson_preview": preview, "raster": result}