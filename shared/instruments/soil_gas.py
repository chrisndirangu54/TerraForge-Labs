from __future__ import annotations

import csv
from pathlib import Path

SOIL_GAS_FIELDS = [
    "sample_id",
    "lon",
    "lat",
    "co2_ppm",
    "helium_ppm",
    "radon_bq_m3",
    "h2s_ppm",
    "ch4_ppm",
]
SUPPORTED_SOIL_GAS_INSTRUMENTS = [
    "RAD7 radon detector",
    "helium leak detector",
    "portable CO2 flux chamber",
    "multi-gas meter",
]


def parse_soil_gas_csv(filepath: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(filepath).open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = dict(raw)
            for key in SOIL_GAS_FIELDS:
                if key in {"sample_id"} or key not in row or row[key] == "":
                    continue
                row[key] = float(row[key])
            rows.append(row)
    return rows
