from __future__ import annotations

import csv
from pathlib import Path


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class GenericCsvParser:
    """Parse tabular CSV/TSV with automatic lon/lat column detection."""

    LON_KEYS = {"lon", "longitude", "lng", "x", "easting", "east"}
    LAT_KEYS = {"lat", "latitude", "y", "northing", "north"}

    def parse(self, filepath: str | Path) -> list[dict]:
        path = Path(filepath)
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        rows: list[dict] = []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            fieldnames = [name.strip() for name in (reader.fieldnames or [])]
            lon_key = self._match_key(fieldnames, self.LON_KEYS)
            lat_key = self._match_key(fieldnames, self.LAT_KEYS)
            id_key = self._match_key(
                fieldnames, {"sample_id", "id", "point_id", "name", "spectrum label"}
            )

            for index, raw in enumerate(reader):
                row = {key.strip(): value for key, value in raw.items()}
                lon = _to_float(row.get(lon_key or "", None)) if lon_key else None
                lat = _to_float(row.get(lat_key or "", None)) if lat_key else None
                sample_id = row.get(id_key) if id_key else None
                numeric_flags = self._numeric_flags(row, lon_key, lat_key)
                rows.append(
                    {
                        "sample_id": sample_id or f"ROW-{index + 1:04d}",
                        "lon": lon if lon is not None else 37.5,
                        "lat": lat if lat is not None else -1.15,
                        **row,
                        "flagged": numeric_flags["flagged"],
                        "flag_reasons": numeric_flags["reasons"],
                    }
                )
        return rows

    def _match_key(self, fieldnames: list[str], candidates: set[str]) -> str | None:
        lowered = {name.lower(): name for name in fieldnames}
        for candidate in candidates:
            if candidate in lowered:
                return lowered[candidate]
        return None

    def _numeric_flags(
        self,
        row: dict,
        lon_key: str | None,
        lat_key: str | None,
    ) -> dict:
        reasons: list[str] = []
        skip = {lon_key, lat_key, "sample_id", "id", "point_id", "name"}
        for key, value in row.items():
            if key in skip or value in (None, ""):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number < 0 and "ppm" in key.lower():
                reasons.append(f"negative_{key}")
        return {"flagged": bool(reasons), "reasons": reasons}