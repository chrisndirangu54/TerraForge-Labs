from __future__ import annotations

from pathlib import Path

from shared.instruments.generic_csv import GenericCsvParser


class InstrumentCsvParser(GenericCsvParser):
    """CSV parser that tags rows with a fixed instrument identifier."""

    INSTRUMENT_ID = "generic_csv"

    def parse(self, filepath: str | Path) -> list[dict]:
        rows = super().parse(filepath)
        for row in rows:
            row["instrument_type"] = self.INSTRUMENT_ID
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
                for row in rows[:200]
            ],
        }


def make_instrument_parser(instrument_id: str) -> type[InstrumentCsvParser]:
    return type(
        f"{instrument_id.title().replace('_', '')}CsvParser",
        (InstrumentCsvParser,),
        {"INSTRUMENT_ID": instrument_id},
    )