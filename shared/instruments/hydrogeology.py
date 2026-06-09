from __future__ import annotations

import csv
from pathlib import Path

SUPPORTED_HYDRO_INSTRUMENTS = [
    "YSI Pro DSS",
    "Solinst Levelogger",
    "Hach HQ40d",
    "Solinst Pumping Test Analyst",
    "Endress+Hauser Promag",
    "tipping_bucket_rain_gauge",
    "METER GS3",
    "Hanna HI98311",
    "Terrameter LS2 aquifer imaging",
]


def parse_hydro(filepath: str) -> dict:
    path = Path(filepath)
    if not path.exists():
        return {
            "water_quality_url": "minio://compliance/water_quality.csv",
            "status": "phase2_stub",
        }
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = dict(raw)
            for key, value in list(row.items()):
                if value == "":
                    continue
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
            rows.append(row)
    return {
        "status": "parsed",
        "instrument_count": len(SUPPORTED_HYDRO_INSTRUMENTS),
        "row_count": len(rows),
        "rows": rows,
        "water_quality_url": "minio://compliance/water_quality.csv",
    }


def parse_levelogger_csv(filepath: str | Path) -> list[dict]:
    path = Path(filepath)
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "timestamp": raw.get("timestamp") or raw.get("date_time"),
                    "water_level_m": float(raw.get("water_level_m", 0)),
                    "temperature_c": float(raw.get("temperature_c", 0)),
                }
            )
    return rows


def parse_pump_test_csv(filepath: str | Path) -> list[dict]:
    path = Path(filepath)
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "elapsed_min": float(raw.get("elapsed_min", 0)),
                    "drawdown_m": float(raw.get("drawdown_m", 0)),
                    "well_id": raw.get("well_id", "PW-1"),
                }
            )
    return rows


def lab_water_quality_schema() -> list[str]:
    return [
        "sample_id",
        "lon",
        "lat",
        "ph",
        "ec_us_cm",
        "tds_mg_l",
        "nitrate_mg_l",
        "fluoride_mg_l",
        "calcium_mg_l",
        "magnesium_mg_l",
        "sodium_mg_l",
        "chloride_mg_l",
        "sulfate_mg_l",
        "bicarbonate_mg_l",
    ]

def parse_hydro(_filepath: str) -> dict:
    return {'water_quality_url': 'minio://compliance/water_quality.csv', 'status': 'phase2_stub'}
