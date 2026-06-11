#!/usr/bin/env python3
"""Run all TerraForge model evaluation benchmarks and emit JSON."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.geobotany_classifier.evaluate import evaluate_geobotany_classifier_stub
from models.grain_segmentation.evaluate import evaluate_grain_model_stub
from models.mineral_classifier.evaluate import evaluate_stub as evaluate_mineral


def run_all() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmarks": {
            "mineral_classifier": evaluate_mineral(),
            "geobotany_classifier": evaluate_geobotany_classifier_stub(),
            "grain_segmentation": evaluate_grain_model_stub(),
        },
    }


def main() -> int:
    results = run_all()
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
