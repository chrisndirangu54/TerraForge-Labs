from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from backend.api.services.storage import get_storage_service
from backend.processing.mapping_stack import layer_catalogue

MATUU_CENTRE = {"lon": 37.5, "lat": -1.15, "elevation_m": 1180}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_matuu_geojson() -> dict[str, Any]:
    path = _repo_root() / "data" / "field" / "matuu_synthetic.geojson"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _borehole_geojson() -> dict[str, Any]:
    boreholes = [
        {
            "id": "BH-MAT-001",
            "lon": 37.48,
            "lat": -1.15,
            "water_level_m": 42.0,
            "aquifer": "fractured_basement",
        },
        {
            "id": "BH-MAT-002",
            "lon": 37.49,
            "lat": -1.14,
            "water_level_m": 39.5,
            "aquifer": "weathered_regolith",
        },
        {
            "id": "BH-MAT-003",
            "lon": 37.47,
            "lat": -1.16,
            "water_level_m": 44.2,
            "aquifer": "fractured_basement",
        },
    ]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [hole["lon"], hole["lat"]]},
                "properties": hole,
            }
            for hole in boreholes
        ],
    }


def _deposit_blocks_geojson() -> dict[str, Any]:
    from backend.api.services.exploration_summary import load_blocks_preview

    blocks = load_blocks_preview(limit=120)
    features: list[dict[str, Any]] = []
    for block in blocks:
        lon = block.get("lon")
        lat = block.get("lat")
        if lon is None or lat is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "properties": block,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _latest_kriging_storage_key() -> str | None:
    storage = get_storage_service()
    keys = [
        key
        for key in storage.list_keys(prefix="kriging_")
        if key.endswith("_mean.tif")
    ]
    if not keys:
        artifacts = _repo_root() / "artifacts"
        if artifacts.exists():
            local = sorted(
                artifacts.glob("kriging_*_mean.tif"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if local:
                return local[0].name
        return None
    return sorted(keys)[-1]


def _build_overlays() -> list[dict[str, Any]]:
    mean_key = _latest_kriging_storage_key()
    if not mean_key:
        return [
            {
                "id": "kriging_grade_heatmap",
                "type": "raster",
                "title": "Kriging grade heatmap",
                "tile_url_template": None,
                "preview_url": None,
                "opacity": 0.65,
                "available": False,
                "storage_key": None,
            }
        ]

    return [
        {
            "id": "kriging_grade_heatmap",
            "type": "raster",
            "title": "Kriging grade heatmap",
            "tile_url_template": f"/mapping/cog/{mean_key}/tiles/{{z}}/{{x}}/{{y}}.png",
            "preview_url": f"/mapping/cog/{mean_key}/preview.png",
            "opacity": 0.65,
            "available": True,
            "storage_key": mean_key,
        }
    ]


def _compute_bounds(feature_layers: dict[str, Any]) -> tuple[list[float], dict[str, float]]:
    lons: list[float] = []
    lats: list[float] = []

    for layer in feature_layers.values():
        if not isinstance(layer, dict):
            continue
        for feature in layer.get("features", []):
            geometry = feature.get("geometry", {})
            if geometry.get("type") != "Point":
                continue
            coords = geometry.get("coordinates", [])
            if len(coords) >= 2:
                lons.append(float(coords[0]))
                lats.append(float(coords[1]))

    if not lons:
        return (
            [37.45, -1.20, 37.55, -1.10],
            dict(MATUU_CENTRE),
        )

    west = min(lons) - 0.01
    east = max(lons) + 0.01
    south = min(lats) - 0.01
    north = max(lats) + 0.01
    return (
        [west, south, east, north],
        {
            "lon": (west + east) / 2,
            "lat": (south + north) / 2,
            "elevation_m": MATUU_CENTRE["elevation_m"],
        },
    )


def build_map_layers_response(*, project_id: str | None = None) -> dict[str, Any]:
    matuu = _load_matuu_geojson()
    catalogue = layer_catalogue()
    feature_layers = {
        "geological:sample_points": matuu,
        "geological:deposit_model_mesh": _deposit_blocks_geojson(),
        "geological:drillhole_traces": _borehole_geojson(),
        "hydrogeology:borehole_water_levels": _borehole_geojson(),
    }
    bounds, center = _compute_bounds(feature_layers)
    return {
        **catalogue,
        "feature_layers": feature_layers,
        "overlays": _build_overlays(),
        "bounds": bounds,
        "center": center,
        "project_id": project_id,
    }