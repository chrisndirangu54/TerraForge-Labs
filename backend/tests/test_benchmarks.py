from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_all_benchmarks_smoke():
    result = subprocess.run(
        [sys.executable, str(ROOT / "benchmarks" / "run_all.py")],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    payload = json.loads(result.stdout)
    assert "timestamp" in payload
    benchmarks = payload["benchmarks"]
    assert "mineral_classifier" in benchmarks
    assert "geobotany_classifier" in benchmarks
    assert "grain_segmentation" in benchmarks
    assert "accuracy" in benchmarks["mineral_classifier"]
    assert "top1_accuracy" in benchmarks["geobotany_classifier"]
    assert "mean_iou" in benchmarks["grain_segmentation"]
