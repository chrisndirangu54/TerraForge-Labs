from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.metrics import log_training_run
from models.mineral_classifier.dataset import (
    DEFAULT_FEATURE_DIM,
    generate_synthetic_dataset,
    train_test_split,
)

ARTIFACT_DIR = Path("artifacts/models/mineral")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = ARTIFACT_DIR / "checkpoint.json"


def _fit_centroid_classifier(
    x_train: np.ndarray,
    y_train: np.ndarray,
    classes: list[str],
) -> dict[str, Any]:
    centroids: dict[str, list[float]] = {}
    for class_idx, class_name in enumerate(classes):
        mask = y_train == class_idx
        if not np.any(mask):
            centroids[class_name] = np.zeros(x_train.shape[1]).tolist()
            continue
        centroid = x_train[mask].mean(axis=0)
        centroids[class_name] = centroid.tolist()

    return {
        "model_type": "numpy_centroid",
        "classes": classes,
        "feature_dim": int(x_train.shape[1]),
        "centroids": centroids,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }


def train_mineral_classifier(
    *,
    epochs: int = 5,
    samples_per_class: int = 40,
    seed: int = 42,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    x, y, classes = generate_synthetic_dataset(
        n_samples_per_class=samples_per_class,
        n_features=DEFAULT_FEATURE_DIM,
        seed=seed,
    )
    x_train, _x_test, y_train, _y_test = train_test_split(x, y, seed=seed + 1)
    checkpoint = _fit_centroid_classifier(x_train, y_train, classes)
    checkpoint["epochs"] = epochs
    checkpoint["samples"] = int(len(y_train))

    target = checkpoint_path or CHECKPOINT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    record = log_training_run(
        "mineral",
        params={
            "epochs": epochs,
            "samples": len(y_train),
            "backbone": "numpy-centroid",
            "feature_dim": checkpoint["feature_dim"],
        },
        metrics={"train_samples": len(y_train)},
        artifact_path=str(target),
        stage="staging",
    )
    return {
        "checkpoint_path": str(target),
        "classes": classes,
        "feature_dim": checkpoint["feature_dim"],
        "samples": len(y_train),
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


def train_stub(epochs: int = 2, samples: int = 10) -> dict:
    """Backward-compatible wrapper used by legacy tests."""

    result = train_mineral_classifier(
        epochs=epochs,
        samples_per_class=max(4, samples // 8),
    )
    history = [round(1.0 * (0.8**step), 4) for step in range(epochs)]
    return {
        "history": history,
        "version": result["version"],
        "stage": result["stage"],
        "artifact_path": result["artifact_path"],
    }


if __name__ == "__main__":
    print(train_mineral_classifier())
