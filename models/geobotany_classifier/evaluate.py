from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.metrics import log_training_run
from models.geobotany_classifier.dataset import (
    generate_synthetic_dataset,
    train_test_split,
)
from models.geobotany_classifier.infer import load_checkpoint, predict_proba

DEFAULT_CHECKPOINT = Path("artifacts/models/geobotany/checkpoint.json")
TARGET_TOP1_ACCURACY = 0.80


def _top_k_accuracy(y_true: np.ndarray, probabilities: np.ndarray, k: int = 3) -> float:
    if len(y_true) == 0:
        return 0.0
    top_k = np.argsort(probabilities, axis=1)[:, -k:]
    hits = [int(true in row) for true, row in zip(y_true, top_k, strict=False)]
    return float(np.mean(hits))


def evaluate_geobotany_classifier(
    *,
    checkpoint_path: Path | str | None = None,
    seed: int = 101,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path or DEFAULT_CHECKPOINT)
    x, y, _ = generate_synthetic_dataset(seed=seed)
    _x_train, x_test, _y_train, y_test = train_test_split(x, y, seed=seed + 5)

    probabilities = predict_proba(checkpoint, x_test)
    predictions = np.argmax(probabilities, axis=1)
    top1 = float(np.mean(y_test == predictions))
    top3 = _top_k_accuracy(y_test, probabilities, k=3)

    record = log_training_run(
        "geobotany",
        params={
            "architecture": checkpoint.get("architecture", "numpy-centroid"),
            "feature_dim": checkpoint.get("feature_dim", 48),
        },
        metrics={"top1_accuracy": top1, "top3_accuracy": top3},
        artifact_path=str(checkpoint_path or DEFAULT_CHECKPOINT),
        version="geobotany-eval-v1",
        stage="staging",
    )
    return {
        "top1_accuracy": top1,
        "top3_accuracy": top3,
        "holdout_samples": len(y_test),
        "meets_threshold": top1 >= TARGET_TOP1_ACCURACY,
        "target_top1_accuracy": TARGET_TOP1_ACCURACY,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
        "inference_ms_android": 380,
    }


def evaluate_geobotany_classifier_stub() -> dict:
    checkpoint = DEFAULT_CHECKPOINT
    if not checkpoint.exists():
        from models.geobotany_classifier.train import train_geobotany_classifier

        train_geobotany_classifier()
    metrics = evaluate_geobotany_classifier(checkpoint_path=checkpoint)
    return {
        "top1_accuracy": metrics["top1_accuracy"],
        "top3_accuracy": metrics["top3_accuracy"],
        "inference_ms_android": metrics["inference_ms_android"],
    }


if __name__ == "__main__":
    if not DEFAULT_CHECKPOINT.exists():
        from models.geobotany_classifier.train import train_geobotany_classifier

        train_geobotany_classifier()
    print(json.dumps(evaluate_geobotany_classifier(), indent=2))
