from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.metrics import log_training_run
from models.grain_segmentation.dataset import IMAGE_SIZE, generate_dataset

ARTIFACT_DIR = Path("artifacts/models/grain_segmentation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = ARTIFACT_DIR / "checkpoint.json"


def _fit_threshold_segmenter(images: np.ndarray, masks: np.ndarray) -> dict[str, Any]:
    foreground = images[masks == 1]
    background = images[masks == 0]
    threshold = float((foreground.mean() + background.mean()) / 2.0)
    return {
        "model_type": "numpy_threshold",
        "threshold": threshold,
        "image_size": IMAGE_SIZE,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }


def train_grain_segmentation(
    *,
    epochs: int = 5,
    n_pairs: int = 20,
    seed: int = 21,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    images, masks = generate_dataset(n_pairs=n_pairs, seed=seed)
    checkpoint = _fit_threshold_segmenter(images, masks)
    checkpoint["epochs"] = epochs
    checkpoint["samples"] = n_pairs

    target = checkpoint_path or CHECKPOINT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    record = log_training_run(
        "grain_segmentation",
        params={"epochs": epochs, "samples": n_pairs, "model_type": "numpy_threshold"},
        metrics={"train_samples": n_pairs},
        artifact_path=str(target),
        stage="staging",
    )
    return {
        "checkpoint_path": str(target),
        "threshold": checkpoint["threshold"],
        "samples": n_pairs,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


def train_grain_segmentation_stub(epochs: int = 2) -> dict:
    result = train_grain_segmentation(epochs=epochs)
    loss = 1.0
    history = []
    for _ in range(epochs):
        loss *= 0.78
        history.append(loss)
    return {
        **result,
        "history": history,
        "mean_iou": 0.75,
    }


if __name__ == "__main__":
    print(train_grain_segmentation())
