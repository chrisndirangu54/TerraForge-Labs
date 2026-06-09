import csv
from pathlib import Path

from backend.processing.deposit_model import generate_deposit_model_files


def test_deposit_model_outputs_valid_files():
    res = generate_deposit_model_files({"job_id": "unit_test_model"})
    assert res["mesh_url"].startswith("minio://")
    csv_path = Path("artifacts/unit_test_model_block_model.csv")
    assert csv_path.exists()
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert all(r["ta_ppm_mean"] != "" for r in rows)
