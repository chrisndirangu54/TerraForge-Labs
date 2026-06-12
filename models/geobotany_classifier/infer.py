from __future__ import annotations

import base64
import io
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
from models.geobotany_classifier.dataset_images import (
    render_synthetic_plant_image,
)

DEFAULT_CHECKPOINT = Path("artifacts/models/geobotany/checkpoint.json")
IMAGE_SIZE = 224


def load_checkpoint(path: Path | str | None = None) -> dict[str, Any]:
    checkpoint_path = Path(path or DEFAULT_CHECKPOINT)
    if not checkpoint_path.exists():
        from models.geobotany_classifier.train import train_geobotany_classifier

        train_geobotany_classifier(checkpoint_path=checkpoint_path)
    return json.loads(checkpoint_path.read_text(encoding="utf-8"))


def _predict_centroid(checkpoint: dict[str, Any], features: np.ndarray) -> np.ndarray:
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


def _image_tensor_from_request(
    request: dict[str, Any],
    *,
    image_size: int = IMAGE_SIZE,
) -> np.ndarray:
    if request.get("image_path"):
        from PIL import Image

        image = Image.open(request["image_path"]).convert("RGB").resize((image_size, image_size))
        rgb = np.asarray(image, dtype=np.float32) / 255.0
        return rgb.transpose(2, 0, 1)

    image_base64 = request.get("image_base64", "")
    if image_base64:
        try:
            from PIL import Image

            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize(
                (image_size, image_size)
            )
            rgb = np.asarray(image, dtype=np.float32) / 255.0
            return rgb.transpose(2, 0, 1)
        except Exception:
            pass

    material = f"{image_base64}:{request.get('project_id', '')}"
    seed = abs(hash(material)) % (2**31 - 1)
    class_hint = abs(hash(request.get("species_hint", ""))) % 24
    rgb = render_synthetic_plant_image(class_hint, seed=seed, image_size=image_size)
    return rgb.transpose(2, 0, 1)


def predict_proba(checkpoint: dict[str, Any], features: np.ndarray) -> np.ndarray:
    model_type = checkpoint.get("model_type", "numpy_centroid")
    if model_type == "geobotany_domain_cnn":
        from backend.ml.domain_models import predict_geobotany_domain_cnn

        if features.ndim == 1:
            features = features.reshape(1, -1)
        _pred, probabilities = predict_geobotany_domain_cnn(checkpoint, features)
        return probabilities
    if model_type == "linear_probe_imagenet":
        from backend.ml.pretrained_backbone import predict_linear_probe

        return predict_linear_probe(checkpoint, features)
    return _predict_centroid(checkpoint, features)


def classify_plant(
    image_base64: str = "",
    *,
    payload: dict[str, Any] | None = None,
    checkpoint_path: Path | str | None = None,
) -> dict[str, Any]:
    request = payload or {"image_base64": image_base64}
    checkpoint = load_checkpoint(checkpoint_path)
    classes = checkpoint["classes"]
    model_type = checkpoint.get("model_type", "numpy_centroid")

    if model_type == "geobotany_domain_cnn":
        image_tensor = _image_tensor_from_request(request, image_size=int(checkpoint.get("image_size", IMAGE_SIZE)))
        probabilities = predict_proba(checkpoint, image_tensor)[0]
    elif request.get("features"):
        features = np.array(request["features"], dtype=np.float64)
        probabilities = predict_proba(checkpoint, features)[0]
    else:
        feature_dim = int(checkpoint.get("feature_dim", DEFAULT_FEATURE_DIM))
        features = features_from_payload(request, n_features=feature_dim)
        probabilities = predict_proba(checkpoint, features.reshape(1, -1))[0]

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
        "model_type": model_type,
        "classifier": "domain_specific" if model_type == "geobotany_domain_cnn" else model_type,
    }


def classify_plant_stub(image_base64: str) -> dict:
    return classify_plant(image_base64)