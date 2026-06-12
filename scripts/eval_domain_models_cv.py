"""Stratified CV evaluation for domain-specific thin-section and spectral models."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        import torch  # noqa: F401
    except ImportError:
        print(json.dumps({"error": "torch not installed"}, indent=2))
        return 1

    from models.spectral_classifier.evaluate import evaluate_spectral_classifier
    from models.thin_section_classifier.evaluate import evaluate_thin_section_classifier

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation": "domain_models_stratified_cv",
        "device": "cuda" if __import__("torch").cuda.is_available() else "cpu",
        "models": {
            "thin_section_cnn": evaluate_thin_section_classifier(
                data_source="corpus",
                n_splits=5,
                epochs=6,
                samples_per_class=80,
            ),
            "spectral_1d_cnn": evaluate_spectral_classifier(
                data_source="corpus",
                n_splits=5,
                epochs=8,
                samples_per_class=120,
            ),
        },
    }

    out_path = ROOT / "artifacts" / "eval_domain_models_cv.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())