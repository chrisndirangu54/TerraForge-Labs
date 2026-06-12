from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.domain_models import predict_spectral_cnn
from models.spectral_classifier.dataset import N_BANDS, generate_spectrum

DEFAULT_CHECKPOINT = Path("artifacts/models/spectral/checkpoint.json")


def load_checkpoint(path: Path | str | None = None) -> dict[str, Any]:
    checkpoint_path = Path(path or DEFAULT_CHECKPOINT)
    if not checkpoint_path.exists():
        from models.spectral_classifier.train import train_spectral_classifier

        train_spectral_classifier(checkpoint_path=checkpoint_path, epochs=6)
    return json.loads(checkpoint_path.read_text(encoding="utf-8"))


def classify_spectrum(
    spectrum: np.ndarray,
    *,
    checkpoint_path: Path | str | None = None,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path)
    classes = checkpoint["classes"]
    if spectrum.ndim == 1:
        spectrum = spectrum.reshape(1, -1)
    predictions, probabilities = predict_spectral_cnn(checkpoint, spectrum.astype(np.float32))
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
        "model_type": checkpoint.get("model_type", "spectral_1d_cnn"),
        "architecture": checkpoint.get("architecture", "Spectral1DCNN"),
        "n_bands": int(checkpoint.get("n_bands", N_BANDS)),
    }


def classify_from_payload(payload: dict[str, Any], **kwargs) -> dict[str, Any]:
    if payload.get("reflectance"):
        spectrum = np.asarray(payload["reflectance"], dtype=np.float32)
    else:
        class_idx = int(payload.get("class_idx", 0))
        spectrum, _ = generate_spectrum(class_idx=class_idx, sample_idx=0)
    return classify_spectrum(spectrum, **kwargs)