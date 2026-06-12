from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from backend.api.services.storage import get_storage_service
from backend.processing.lidar_pipeline import process_lidar_to_cogs

LIDAR_GROUND_RESOLUTION_M = 0.5
LIDAR_MIN_POINTS_PER_M2 = 4
LIDAR_MAX_FILE_SIZE_GB = 5


@dataclass
class LiDARResult:
    dem_url: str
    dsm_url: str
    chm_url: str
    lineaments_url: str


def _minio_url(storage_key: str) -> str:
    return f"minio://spectral/{storage_key}"


def _ensure_uploaded(filepath: Path, *, project_id: str) -> str:
    storage_key = f"lidar/{project_id}/{filepath.name}"
    storage = get_storage_service()
    if filepath.exists() and not storage.exists(storage_key):
        storage.put(
            storage_key,
            filepath.read_bytes(),
            content_type="application/octet-stream",
        )
    return storage_key


def _write_lineaments_geojson(storage_key: str, bounds: list[float]) -> str:
    west, south, east, north = bounds
    feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [west, (south + north) / 2],
                        [east, (south + north) / 2],
                    ],
                },
                "properties": {"source": "slope_break_stub", "confidence": 0.55},
            }
        ],
    }
    storage = get_storage_service()
    storage.put(
        storage_key,
        json.dumps(feature).encode("utf-8"),
        content_type="application/geo+json",
    )
    return storage_key


def parse(filepath: str, crs: str = "EPSG:4326", project_id: str = "spectral") -> LiDARResult:
    path = Path(filepath)
    if path.suffix.lower() not in {".las", ".laz"}:
        raise ValueError("Unsupported LiDAR format; expected .las or .laz")

    storage_key = _ensure_uploaded(path, project_id=project_id)
    result = process_lidar_to_cogs(
        {
            "project_id": project_id,
            "storage_key": storage_key,
            "resolution_m": LIDAR_GROUND_RESOLUTION_M,
        }
    )
    lineaments_key = f"lidar/{project_id}/{path.stem}_lineaments.geojson"
    _write_lineaments_geojson(lineaments_key, result["bounds"])

    return LiDARResult(
        dem_url=_minio_url(result["dtm"]["storage_key"]),
        dsm_url=_minio_url(result["dsm"]["storage_key"]),
        chm_url=_minio_url(result["chm"]["storage_key"]),
        lineaments_url=_minio_url(lineaments_key),
    )