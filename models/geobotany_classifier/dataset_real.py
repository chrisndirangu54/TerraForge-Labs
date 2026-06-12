from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from models.geobotany_classifier.dataset import GEOBOTANY_CLASSES


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_gbif_path() -> Path:
    candidates = [
        _repo_root() / "data" / "geobotany" / "gbif_kenya_metallophytes.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "GBIF dataset not found; run scripts/datasets/pull_gbif.py"
    )


def _species_to_class(species: str | None) -> int:
    if not species:
        return 0
    lowered = species.lower()
    for index, name in enumerate(GEOBOTANY_CLASSES):
        if name.lower() in lowered or lowered in name.lower():
            return index
    return abs(hash(lowered)) % len(GEOBOTANY_CLASSES)


def load_real_dataset(
    *,
    gbif_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = gbif_path or _default_gbif_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[list[float]] = []
    labels: list[int] = []
    for record in payload.get("records", []):
        lat = record.get("decimalLatitude")
        lon = record.get("decimalLongitude")
        if lat is None or lon is None:
            continue
        year = float(record.get("year") or 2000)
        rows.append([float(lon), float(lat), year / 2100.0, 1.0])
        labels.append(_species_to_class(record.get("species")))
    if not rows:
        raise ValueError(f"No GBIF records with coordinates in {path}")
    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(labels, dtype=np.int64),
        list(GEOBOTANY_CLASSES),
    )