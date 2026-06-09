from __future__ import annotations

import csv
from pathlib import Path

from shared.constants import GEMPY_DEPTH_EXTENT_M, GEMPY_RESOLUTION, TA_GRADE_THRESHOLD_PPM

ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)


def generate_deposit_model_files(payload: dict) -> dict:
    base = payload.get("job_id", "deposit_model")
    obj_path = ARTIFACT_DIR / f"{base}.obj"
    csv_path = ARTIFACT_DIR / f"{base}_block_model.csv"
    prob_path = ARTIFACT_DIR / f"{base}_probability.tif"

    obj_path.write_text("\n".join(["o TerraforgeDeposit", "v 0 0 0", "v 1 0 0", "v 0 1 0", "f 1 2 3"]))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["x", "y", "z", "ta_ppm_mean", "ta_ppm_p10", "ta_ppm_p90", "unit"])
        writer.writeheader()
        for i in range(20):
            writer.writerow({"x": i, "y": i, "z": i % 5, "ta_ppm_mean": 120 + i, "ta_ppm_p10": 90 + i, "ta_ppm_p90": 150 + i, "unit": "pegmatite"})

    prob_path.write_text("probability-grid-placeholder")

    return {
        "mesh_url": f"minio://models/{obj_path.name}",
        "block_model_url": f"minio://models/{csv_path.name}",
        "probability_map_url": f"minio://models/{prob_path.name}",
        "summary": {
            "estimated_deposit_volume_m3": 25000,
            "mean_grade_ta_ppm": 132,
            "resource_category": "inferred",
            "resolution": GEMPY_RESOLUTION,
            "depth_extent_m": GEMPY_DEPTH_EXTENT_M,
            "ta_grade_threshold_ppm": TA_GRADE_THRESHOLD_PPM,
        },
    }
