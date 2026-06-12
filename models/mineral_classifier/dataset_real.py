from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from shared.constants import MINERAL_CLASSES

FEATURE_KEYS = (
    "ta_ppm",
    "nb_ppm",
    "sn_ppm",
    "fe_ppm",
    "susceptibility_si",
    "ph",
    "conductivity_us_cm",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_geojson_path() -> Path:
    candidates = [
        _repo_root() / "data" / "field" / "matuu_synthetic.geojson",
        _repo_root() / "tests" / "fixtures" / "matuu_synthetic.geojson",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("matuu_synthetic.geojson not found; run scripts/datasets/pull_field_data.py")


def _infer_label(properties: dict[str, Any]) -> int:
    ta = float(properties.get("ta_ppm", 0.0))
    nb = float(properties.get("nb_ppm", 0.0))
    fe = float(properties.get("fe_ppm", 0.0))
    sn = float(properties.get("sn_ppm", 0.0))
    if ta >= 180:
        return MINERAL_CLASSES.index("tantalite") if "tantalite" in MINERAL_CLASSES else 0
    if nb >= 1200:
        return MINERAL_CLASSES.index("columbite") if "columbite" in MINERAL_CLASSES else 1
    if fe >= 50000:
        return MINERAL_CLASSES.index("magnetite") if "magnetite" in MINERAL_CLASSES else 2
    if sn >= 80:
        return MINERAL_CLASSES.index("cassiterite") if "cassiterite" in MINERAL_CLASSES else 3
    return MINERAL_CLASSES.index("gangue") if "gangue" in MINERAL_CLASSES else 0


def load_real_dataset(
    *,
    geojson_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = geojson_path or _default_geojson_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[list[float]] = []
    labels: list[int] = []
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        vector = [float(props.get(key, 0.0)) for key in FEATURE_KEYS]
        rows.append(vector)
        labels.append(_infer_label(props))
    if not rows:
        raise ValueError(f"No features found in {path}")
    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(labels, dtype=np.int64),
        list(MINERAL_CLASSES),
    )