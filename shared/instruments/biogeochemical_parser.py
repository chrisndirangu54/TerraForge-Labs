from __future__ import annotations

from pathlib import Path

from shared.instruments.biogeochemical import parse_icp_ms_csv, summarise_biogeochem


class BiogeochemicalParser:
    def parse(self, filepath: str | Path) -> list[dict]:
        rows = parse_icp_ms_csv(filepath)
        for index, row in enumerate(rows):
            row.setdefault("sample_id", row.get("sample_id") or f"BIO-{index + 1:04d}")
            row.setdefault("lon", float(row.get("lon", 37.5)))
            row.setdefault("lat", float(row.get("lat", -1.15)))
            row["flagged"] = bool(row.get("hyperaccumulator", False))
        return rows

    def to_geojson(self, rows: list[dict], crs: str = "EPSG:4326") -> dict:
        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": crs}},
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                    "properties": {k: v for k, v in r.items() if k not in {"lon", "lat"}},
                }
                for r in rows
            ],
        }

    def summarise(self, rows: list[dict], element: str = "Cu") -> dict:
        return summarise_biogeochem(rows, element=element)