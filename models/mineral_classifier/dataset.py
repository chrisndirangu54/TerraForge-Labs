from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from shared.constants import MINERAL_CLASSES

DEFAULT_FEATURE_DIM = 32
DEFAULT_SAMPLES_PER_CLASS = 40


def _class_seed(class_idx: int, base_seed: int) -> int:
    digest = hashlib.sha256(f"{base_seed}:{class_idx}".encode()).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def generate_synthetic_dataset(
    *,
    n_samples_per_class: int = DEFAULT_SAMPLES_PER_CLASS,
    n_features: int = DEFAULT_FEATURE_DIM,
    seed: int = 42,
    noise_std: float = 0.35,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Generate separable synthetic mineral feature vectors for CI-friendly training."""

    classes = list(MINERAL_CLASSES)
    rows: list[np.ndarray] = []
    labels: list[int] = []

    for class_idx, _class_name in enumerate(classes):
        rng = np.random.default_rng(_class_seed(class_idx, seed))
        centroid = rng.normal(loc=class_idx * 2.5, scale=0.4, size=n_features)
        samples = rng.normal(
            loc=centroid,
            scale=noise_std,
            size=(n_samples_per_class, n_features),
        )
        rows.append(samples)
        labels.extend([class_idx] * n_samples_per_class)

    x = np.vstack(rows).astype(np.float64)
    y = np.array(labels, dtype=np.int64)
    permutation = np.random.default_rng(seed).permutation(len(y))
    return x[permutation], y[permutation], classes


def features_from_payload(
    payload: dict[str, Any], n_features: int = DEFAULT_FEATURE_DIM
) -> np.ndarray:
    """Derive deterministic feature vectors from image/hash payloads when raw tensors are absent."""

    material = (
        f"{payload.get('image_base64', '')[:256]}:"
        f"{payload.get('image_path', '')}:"
        f"{payload.get('project_id', '')}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big") % (2**31 - 1)
    rng = np.random.default_rng(seed)
    return rng.normal(size=n_features).astype(np.float64)


def train_test_split(
    x: np.ndarray,
    y: np.ndarray,
    *,
    test_ratio: float = 0.25,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(y))
    split = max(1, int(len(y) * (1.0 - test_ratio)))
    train_idx = indices[:split]
    test_idx = indices[split:]
    if len(test_idx) == 0:
        test_idx = indices[-1:]
    return x[train_idx], x[test_idx], y[train_idx], y[test_idx]
