from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from models.geobotany_classifier.dataset import (
    GEOBOTANY_CONFIDENCE_THRESHOLD,
    GEOBOTANY_MODEL_VERSION,
    DEFAULT_FEATURE_DIM,
    features_from_payload,
    get_affinity,
)

DEFAULT_CHECKPOINT = Path("artifacts/models/geobotany/checkpoint.json")


def load_checkpoint(path: Path | str | None = None) -> dict[str, Any]:
    checkpoint_path = Path(path or DEFAULT_CHECKPOINT)
    if not checkpoint_path.exists():
        from models.geobotany_classifier.train import train_geobotany_classifier

        train_geobotany_classifier(checkpoint_path=checkpoint_path)
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


def classify_plant(
    image_base64: str = "",
    *,
    payload: dict[str, Any] | None = None,
    checkpoint_path: Path | str | None = None,
) -> dict[str, Any]:
    request = payload or {"image_base64": image_base64}
    checkpoint = load_checkpoint(checkpoint_path)
    classes = checkpoint["classes"]
    feature_dim = int(checkpoint.get("feature_dim", DEFAULT_FEATURE_DIM))

    if request.get("features"):
        features = np.array(request["features"], dtype=np.float64)
    else:
        features = features_from_payload(request, n_features=feature_dim)

    probabilities = predict_proba(checkpoint, features)[0]
    ranked_idx = np.argsort(probabilities)[::-1]
    species = classes[int(ranked_idx[0])]
    confidence = float(probabilities[int(ranked_idx[0])])
    accepted_species = (
        species
        if confidence >= GEOBOTANY_CONFIDENCE_THRESHOLD
        else "unknown_vegetation"
    )

    return {
        "species": accepted_species,
        "confidence": round(confidence, 4),
        "mineral_affinity": get_affinity(accepted_species),
        "recommended_action": (
            "Collect leaf tissue sample and run XRF transect"
            if accepted_species != "unknown_vegetation"
            else "Re-photograph with closer framing and geotag"
        ),
        "top3": [
            {
                "species": classes[int(idx)],
                "score": round(float(probabilities[int(idx)]), 4),
            }
            for idx in ranked_idx[:3]
        ],
        "model_version": checkpoint.get("version", GEOBOTANY_MODEL_VERSION),
        "model_type": checkpoint.get("model_type", "numpy_centroid"),
    }


def classify_plant_stub(image_base64: str) -> dict:
    return classify_plant(image_base64)
