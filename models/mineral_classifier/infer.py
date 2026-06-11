from __future__ import annotations

from backend.processing.gpu_classifier import classify_gpu


def classify_mineral_cloud(payload: dict) -> dict:
    return classify_gpu("mineral", payload)
