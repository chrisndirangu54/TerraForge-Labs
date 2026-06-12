from __future__ import annotations

import json
from pathlib import Path


class GenericGeoJsonParser:
    def parse(self, filepath: str | Path) -> list[dict]:
        payload = json.loads(Path(filepath).read_text(encoding="utf-8"))
        rows: list[dict] = []
        features = payload.get("features", [])
        for index, feature in enumerate(features):
            props = feature.get("properties") or {}
            coords = (feature.get("geometry") or {}).get("coordinates") or [37.5, -1.15]
            rows.append(
                {
                    "sample_id": props.get("sample_id") or props.get("id") or f"G-{index + 1:03d}",
                    "lon": float(coords[0]),
                    "lat": float(coords[1]),
                    **props,
                    "flagged": bool(props.get("flagged", False)),
                }
            )
        return rows

    def to_geojson(self, rows: list[dict], crs: str = "EPSG:4326") -> dict:
        return {
            "type": "FeatureCollection",
            "crs": crs,
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row.get("lon", 0), row.get("lat", 0)],
                    },
                    "properties": row,
                }
                for row in rows
            ],
        }