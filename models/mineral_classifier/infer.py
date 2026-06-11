from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.processing.gpu_classifier import classify_gpu
from models.mineral_classifier.dataset import DEFAULT_FEATURE_DIM, features_from_payload

DEFAULT_CHECKPOINT = Path("artifacts/models/mineral/checkpoint.json")


def load_checkpoint(path: Path | str | None = None) -> dict[str, Any]:
    checkpoint_path = Path(path or DEFAULT_CHECKPOINT)
    if not checkpoint_path.exists():
        from models.mineral_classifier.train import train_mineral_classifier

        train_mineral_classifier(checkpoint_path=checkpoint_path)
    return json.loads(checkpoint_path.read_text(encoding="utf-8"))


def predict_proba(checkpoint: dict[str, Any], features: np.ndarray) -> np.ndarray:
    classes = checkpoint["classes"]
    centroids = np.array(
        [checkpoint["centroids"][name] for name in classes], dtype=np.float64
    )
    if features.ndim == 1:
        features = features.reshape(1, -1)

    distances = np.linalg.norm(features[:, None, :] - centroids[None, :, :], axis=2)
    scores = 1.0 / (distances + 1e-6)
    totals = scores.sum(axis=1, keepdims=True)
    return scores / np.maximum(totals, 1e-9)


def classify_mineral(
    payload: dict[str, Any],
    *,
    checkpoint_path: Path | str | None = None,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path)
    classes = checkpoint["classes"]
    feature_dim = int(checkpoint.get("feature_dim", DEFAULT_FEATURE_DIM))

    if payload.get("features"):
        features = np.array(payload["features"], dtype=np.float64)
    else:
        features = features_from_payload(payload, n_features=feature_dim)

    probabilities = predict_proba(checkpoint, features)[0]
    ranked_idx = np.argsort(probabilities)[::-1]
    primary_idx = int(ranked_idx[0])
    label = classes[primary_idx]
    confidence = float(probabilities[primary_idx])

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "top3": [
            {
                "label": classes[int(idx)],
                "score": round(float(probabilities[int(idx)]), 4),
            }
            for idx in ranked_idx[:3]
        ],
        "model_type": checkpoint.get("model_type", "numpy-centroid"),
        "checkpoint_path": str(checkpoint_path or DEFAULT_CHECKPOINT),
    }


def classify_mineral_cloud(payload: dict) -> dict:
    return classify_gpu("mineral", payload)
