from __future__ import annotations

import csv
from pathlib import Path

HYPERACCUMULATOR_BCF_THRESHOLD = 10
STRONG_SIGNAL_BCF_THRESHOLD = 5
SOIL_PLANT_JOIN_RADIUS_M = 50
ICP_MS_DETECTION_LIMIT_PPB = {
    "Cu": 0.1,
    "Co": 0.05,
    "Ni": 0.1,
    "Zn": 0.5,
    "Au": 0.001,
    "Ag": 0.01,
    "U": 0.005,
    "Mo": 0.02,
}
REQUIRED_BIOGEOCHEM_FIELDS = {"species_name", "plant_part"}


def parse_icp_ms_csv(filepath: str | Path) -> list[dict]:
    rows: list[dict] = []
    with open(filepath, newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = dict(raw)
            missing = REQUIRED_BIOGEOCHEM_FIELDS - row.keys()
            if missing:
                raise ValueError(
                    f"Missing biogeochemical field(s): {', '.join(sorted(missing))}"
                )
            for key, value in list(row.items()):
                if (
                    key
                    in {"species_name", "plant_part", "sample_id", "collector", "date"}
                    or value == ""
                ):
                    continue
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
            rows.append(row)
    return rows


def calculate_bcf(plant_ppm: float, soil_ppm: float) -> float:
    if soil_ppm <= 0:
        return 0.0
    return plant_ppm / soil_ppm


def calculate_transfer_coefficient(leaf_ppm: float, root_ppm: float) -> float:
    if root_ppm <= 0:
        return 0.0
    return leaf_ppm / root_ppm


def summarise_biogeochem(rows: list[dict], element: str = "Cu") -> dict:
    plant_key = f"plant_{element.lower()}_ppm"
    soil_key = f"soil_{element.lower()}_ppm"
    bcf_values = [
        calculate_bcf(float(r.get(plant_key, 0)), float(r.get(soil_key, 0)))
        for r in rows
    ]
    max_bcf = max(bcf_values) if bcf_values else 0.0
    average_bcf = sum(bcf_values) / len(bcf_values) if bcf_values else 0.0
    return {
        "element": element,
        "sample_count": len(rows),
        "max_bcf": round(max_bcf, 3),
        "average_bcf": round(average_bcf, 3),
        "strong_signal_count": sum(
            1 for value in bcf_values if value >= STRONG_SIGNAL_BCF_THRESHOLD
        ),
        "hyperaccumulator_count": sum(
            1 for value in bcf_values if value >= HYPERACCUMULATOR_BCF_THRESHOLD
        ),
        "join_radius_m": SOIL_PLANT_JOIN_RADIUS_M,
        "kriged_map_url": f"minio://geobotany/{element.lower()}_biogeochem_anomaly.tif",
    }
