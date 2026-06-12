from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.domain_models import predict_thin_section_cnn
from models.thin_section_classifier.dataset import (
    IMAGE_SIZE,
    generate_labeled_pair,
)

DEFAULT_CHECKPOINT = Path("artifacts/models/thin_section/checkpoint.json")


def load_checkpoint(path: Path | str | None = None) -> dict[str, Any]:
    checkpoint_path = Path(path or DEFAULT_CHECKPOINT)
    if not checkpoint_path.exists():
        from models.thin_section_classifier.train import train_thin_section_classifier

        train_thin_section_classifier(checkpoint_path=checkpoint_path, epochs=4)
    return json.loads(checkpoint_path.read_text(encoding="utf-8"))


def classify_from_array(
    pair: np.ndarray,
    *,
    checkpoint_path: Path | str | None = None,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path)
    classes = checkpoint["classes"]
    if pair.ndim == 2:
        pair = pair[None, ...]
    predictions, probabilities = predict_thin_section_cnn(checkpoint, pair.astype(np.float32))
    primary = int(predictions[0])
    ranked = np.argsort(probabilities[0])[::-1]
    return {
        "label": classes[primary],
        "confidence": round(float(probabilities[0, primary]), 4),
        "top3": [
            {
                "label": classes[int(idx)],
                "score": round(float(probabilities[0, int(idx)]), 4),
            }
            for idx in ranked[:3]
        ],
        "model_type": checkpoint.get("model_type", "thin_section_cnn"),
        "architecture": checkpoint.get("architecture", "ThinSectionCNN"),
    }


def classify_from_paths(ppl_path: str, xpl_path: str, **kwargs) -> dict[str, Any]:
    from PIL import Image

    ppl = np.asarray(Image.open(ppl_path).convert("L").resize((IMAGE_SIZE, IMAGE_SIZE))) / 255.0
    xpl = np.asarray(Image.open(xpl_path).convert("L").resize((IMAGE_SIZE, IMAGE_SIZE))) / 255.0
    pair = np.stack([ppl, xpl], axis=0).astype(np.float32)
    return classify_from_array(pair, **kwargs)


def classify_stub(class_idx: int = 0, sample_idx: int = 0) -> dict[str, Any]:
    pair, _ = generate_labeled_pair(class_idx=class_idx, sample_idx=sample_idx)
    return classify_from_array(pair)