from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from models.mineral_classifier.dataset_real import FEATURE_KEYS, _infer_label, _repo_root
from shared.constants import MINERAL_CLASSES

FEATURE_DIM = len(FEATURE_KEYS) + 1


def _usgs_signatures_path() -> Path:
    candidates = [
        _repo_root() / "data" / "sota" / "usgs_mineral_signatures.json",
        _repo_root() / "tests" / "fixtures" / "usgs_mineral_signatures.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("USGS mineral signatures fixture missing")


def _load_usgs_prototypes() -> dict[str, np.ndarray]:
    payload = json.loads(_usgs_signatures_path().read_text(encoding="utf-8"))
    prototypes: dict[str, np.ndarray] = {}
    for mineral, props in (payload.get("minerals") or {}).items():
        vector = [float(props.get(key, 0.0)) for key in FEATURE_KEYS]
        vector.append(float(props.get("reflectance_2200nm", 0.5)))
        prototypes[mineral] = np.asarray(vector, dtype=np.float64)
    return prototypes


def load_sota_dataset() -> tuple[np.ndarray, np.ndarray, list[str]]:
    from models.mineral_classifier.dataset_real import _default_geojson_path

    geojson = json.loads(_default_geojson_path().read_text(encoding="utf-8"))
    prototypes = _load_usgs_prototypes()
    rows: list[np.ndarray] = []
    labels: list[int] = []
    classes = list(MINERAL_CLASSES)

    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        sample = np.asarray(
            [float(props.get(key, 0.0)) for key in FEATURE_KEYS] + [0.5],
            dtype=np.float64,
        )
        label_name = classes[_infer_label(props)]
        prototype = prototypes.get(label_name, prototypes.get("unknown"))
        # Blend field sample with USGS SOTA prototype (pretrained prior).
        blended = 0.65 * sample + 0.35 * prototype
        rows.append(blended)
        labels.append(classes.index(label_name))

    if not rows:
        raise ValueError("No SOTA mineral samples available")
    return np.vstack(rows), np.asarray(labels, dtype=np.int64), classes