from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from models.geobotany_classifier.dataset import GEOBOTANY_CLASSES

FEATURE_DIM = 8


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _inat_path() -> Path | None:
    candidates = [
        _repo_root() / "data" / "geobotany" / "inaturalist_kenya_plants.json",
        _repo_root() / "tests" / "fixtures" / "inaturalist_kenya_sample.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _gbif_path() -> Path:
    from models.geobotany_classifier.dataset_real import _default_gbif_path

    return _default_gbif_path()


def _species_to_class(species: str | None) -> int:
    if not species:
        return GEOBOTANY_CLASSES.index("unknown_vegetation")
    lowered = species.lower().replace(" ", "_")
    for index, name in enumerate(GEOBOTANY_CLASSES):
        token = name.lower()
        if token in lowered or lowered in token:
            return index
    return abs(hash(lowered)) % len(GEOBOTANY_CLASSES)


def load_sota_dataset() -> tuple[np.ndarray, np.ndarray, list[str]]:
    rows: list[list[float]] = []
    labels: list[int] = []

    gbif = json.loads(_gbif_path().read_text(encoding="utf-8"))
    for record in gbif.get("records", []):
        lat = record.get("decimalLatitude")
        lon = record.get("decimalLongitude")
        if lat is None or lon is None:
            continue
        rows.append(
            [
                float(lon),
                float(lat),
                float(record.get("year") or 2018) / 2100.0,
                1.0,
                0.8,
                0.2,
                0.5,
                0.1,
            ]
        )
        labels.append(_species_to_class(record.get("species")))

    inat_path = _inat_path()
    if inat_path is not None:
        inat = json.loads(inat_path.read_text(encoding="utf-8"))
        for record in inat.get("results", []):
            lat = record.get("latitude") or record.get("decimalLatitude")
            lon = record.get("longitude") or record.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            quality = float(record.get("quality_grade_score", 0.9))
            rows.append(
                [
                    float(lon),
                    float(lat),
                    float(record.get("observed_on_year") or 2020) / 2100.0,
                    quality,
                    0.9,
                    0.4,
                    0.7,
                    0.3,
                ]
            )
            labels.append(_species_to_class(record.get("species_guess") or record.get("species")))

    if not rows:
        raise ValueError("No SOTA geobotany records available")
    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(labels, dtype=np.int64),
        list(GEOBOTANY_CLASSES),
    )