from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.metrics import log_training_run
from models.grain_segmentation.dataset import generate_dataset
from models.grain_segmentation.infer import load_checkpoint, segment_image

DEFAULT_CHECKPOINT = Path("artifacts/models/grain_segmentation/checkpoint.json")
TARGET_MEAN_IOU = 0.70


def _iou(prediction: np.ndarray, target: np.ndarray) -> float:
    pred = prediction.astype(bool)
    truth = target.astype(bool)
    intersection = np.logical_and(pred, truth).sum()
    union = np.logical_or(pred, truth).sum()
    if union == 0:
        return 1.0
    return float(intersection / union)


def evaluate_grain_segmentation(
    *,
    checkpoint_path: Path | str | None = None,
    seed: int = 31,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path or DEFAULT_CHECKPOINT)
    images, masks = generate_dataset(n_pairs=20, seed=seed)
    scores = []
    for image, mask in zip(images, masks, strict=False):
        result = segment_image(image, checkpoint=checkpoint)
        scores.append(_iou(result["mask"], mask))

    mean_iou = float(np.mean(scores))
    record = log_training_run(
        "grain_segmentation",
        params={"model_type": checkpoint.get("model_type", "numpy_threshold")},
        metrics={"mean_iou": mean_iou, "holdout_pairs": len(scores)},
        artifact_path=str(checkpoint_path or DEFAULT_CHECKPOINT),
        version="grain-eval-v1",
        stage="staging",
    )
    return {
        "mean_iou": mean_iou,
        "holdout_pairs": len(scores),
        "meets_threshold": mean_iou >= TARGET_MEAN_IOU,
        "target_mean_iou": TARGET_MEAN_IOU,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


def evaluate_grain_model_stub() -> dict:
    checkpoint = DEFAULT_CHECKPOINT
    if not checkpoint.exists():
        from models.grain_segmentation.train import train_grain_segmentation

        train_grain_segmentation()
    metrics = evaluate_grain_segmentation(checkpoint_path=checkpoint)
    return {
        "mean_iou": metrics["mean_iou"],
        "modal_error_pct": round(max(0.0, (1.0 - metrics["mean_iou"]) * 10), 1),
    }


if __name__ == "__main__":
    if not DEFAULT_CHECKPOINT.exists():
        from models.grain_segmentation.train import train_grain_segmentation

        train_grain_segmentation()
    print(json.dumps(evaluate_grain_segmentation(), indent=2))
