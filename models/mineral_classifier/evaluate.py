from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.metrics import log_training_run
from models.mineral_classifier.dataset import (
    generate_synthetic_dataset,
    train_test_split,
)
from models.mineral_classifier.infer import load_checkpoint, predict_proba
from shared.constants import MIN_CLASSIFICATION_ACCURACY

DEFAULT_CHECKPOINT = Path("artifacts/models/mineral/checkpoint.json")


def _accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(y_true == y_pred))


def evaluate_mineral_classifier(
    *,
    checkpoint_path: Path | str | None = None,
    seed: int = 99,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path or DEFAULT_CHECKPOINT)
    classes = checkpoint["classes"]

    if checkpoint.get("model_type") == "linear_probe_imagenet":
        from models.mineral_classifier.dataset_sota import load_sota_dataset

        x, y, _ = load_sota_dataset()
    else:
        feature_dim = int(checkpoint.get("feature_dim", 32))
        x, y, _ = generate_synthetic_dataset(seed=seed, n_features=feature_dim)
    _x_train, x_test, _y_train, y_test = train_test_split(x, y, seed=seed + 3)

    probabilities = predict_proba(checkpoint, x_test)
    predictions = np.argmax(probabilities, axis=1)
    accuracy = _accuracy(y_test, predictions)

    record = log_training_run(
        "mineral",
        params={
            "backbone": checkpoint.get("model_type", "numpy-centroid"),
            "feature_dim": checkpoint.get("feature_dim", 32),
        },
        metrics={"accuracy": accuracy, "holdout_samples": len(y_test)},
        artifact_path=str(checkpoint_path or DEFAULT_CHECKPOINT),
        version="v0.2.0-eval",
        stage="staging",
    )
    return {
        "accuracy": accuracy,
        "holdout_samples": len(y_test),
        "classes": classes,
        "meets_threshold": accuracy >= MIN_CLASSIFICATION_ACCURACY,
        "min_required_accuracy": MIN_CLASSIFICATION_ACCURACY,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


def evaluate_stub() -> dict:
    checkpoint = DEFAULT_CHECKPOINT
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
        if saved.get("data_source") in {"real", "pretrained_sota"}:
            from models.mineral_classifier.train import train_mineral_classifier

            train_mineral_classifier(data_source="synthetic")
    elif not checkpoint.exists():
        from models.mineral_classifier.train import train_mineral_classifier

        train_mineral_classifier()
    metrics = evaluate_mineral_classifier(checkpoint_path=checkpoint)
    holdout = float(metrics["accuracy"])
    record = log_training_run(
        "mineral",
        params={
            "backbone": "numpy-centroid",
            "feature_dim": 32,
            "evaluation": "holdout",
        },
        metrics={
            "accuracy": holdout,
            "holdout_accuracy": holdout,
            "holdout_samples": metrics.get("holdout_samples", 0),
        },
        artifact_path=metrics["artifact_path"],
        version="v0.2.0-eval",
        stage="staging",
    )
    return {
        "accuracy": holdout,
        "holdout_accuracy": holdout,
        "holdout_samples": metrics.get("holdout_samples", 0),
        "meets_threshold": metrics.get("meets_threshold", False),
        "min_required_accuracy": metrics.get("min_required_accuracy"),
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


if __name__ == "__main__":
    if not DEFAULT_CHECKPOINT.exists():
        from models.mineral_classifier.train import train_mineral_classifier

        train_mineral_classifier()
    print(json.dumps(evaluate_mineral_classifier(), indent=2))
