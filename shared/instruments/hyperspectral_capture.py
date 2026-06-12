from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.instruments.hyperspectral import MINERAL_MAP_CLASSES, parse_envi


def parse_hyperspectral_pair(
    hdr_path: str | Path,
    img_path: str | Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    hdr = Path(hdr_path)
    companion = Path(img_path) if img_path else _resolve_envi_companion(hdr)
    result = parse_envi(str(hdr), str(companion))

    row: dict[str, Any] = {
        "sample_id": hdr.stem,
        "lon": 37.5,
        "lat": -1.15,
        "bands": result.get("bands"),
        "classification": result.get("classification"),
        "mineral_map_url": result.get("mineral_map_url"),
        "hdr_path": result.get("hdr"),
        "img_path": result.get("img"),
        "flagged": False,
    }
    preview = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
                "properties": {
                    "name": hdr.stem,
                    "bands": row["bands"],
                    "classification": row["classification"],
                },
            }
        ],
    }
    spectral = {
        **result,
        "classes": MINERAL_MAP_CLASSES,
        "bounds": [37.45, -1.20, 37.55, -1.10],
    }
    return [row], {
        "validation": {"warnings": [], "flagged_count": 0},
        "geojson_preview": preview,
        "spectral": spectral,
    }


def _resolve_envi_companion(hdr: Path) -> Path:
    for suffix in (".img", ".dat", ".raw"):
        candidate = hdr.with_suffix(suffix)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Missing ENVI image companion for {hdr.name}")