from __future__ import annotations

from pathlib import Path

from shared.instruments.generic_csv import GenericCsvParser
from shared.instruments.thin_section import classify_thin_section

IMAGE_SUFFIXES = {".ppl", ".xpl", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


class PetrographicParser:
    """PPL/XPL thin-section pair classifier with CSV metadata fallback."""

    def parse(
        self,
        filepath: str | Path,
        companion_path: str | Path | None = None,
    ) -> list[dict]:
        path = Path(filepath)
        companion = Path(companion_path) if companion_path else None

        if path.suffix.lower() in IMAGE_SUFFIXES and companion and companion.exists():
            return [self._classify_pair(path, companion)]

        if companion and companion.suffix.lower() in IMAGE_SUFFIXES and path.exists():
            return [self._classify_pair(path, companion)]

        rows = GenericCsvParser().parse(path)
        for row in rows:
            row["instrument_type"] = "petrographic"
        return rows

    def _classify_pair(self, primary: Path, secondary: Path) -> dict:
        ppl, xpl = self._ordered_pair(primary, secondary)
        result = classify_thin_section(str(ppl), str(xpl))
        return {
            "sample_id": ppl.stem,
            "lon": 37.5,
            "lat": -1.15,
            "predicted_mineral": result.get("label"),
            "confidence": result.get("confidence"),
            "top3": result.get("top3", []),
            "model_type": result.get("model_type"),
            "ppl_file": ppl.name,
            "xpl_file": xpl.name,
            "instrument_type": "petrographic",
            "flagged": float(result.get("confidence", 0)) < 0.5,
        }

    def _ordered_pair(self, first: Path, second: Path) -> tuple[Path, Path]:
        order = {".ppl": 0, ".png": 0, ".jpg": 0, ".jpeg": 0, ".tif": 0, ".tiff": 0}
        first_rank = 0 if first.suffix.lower() == ".ppl" else 1
        second_rank = 0 if second.suffix.lower() == ".ppl" else 1
        if first.suffix.lower() == ".xpl":
            first_rank = 2
        if second.suffix.lower() == ".xpl":
            second_rank = 2
        if first_rank <= second_rank:
            return first, second
        return second, first

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