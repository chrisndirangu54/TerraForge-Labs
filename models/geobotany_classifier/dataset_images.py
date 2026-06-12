from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from models.geobotany_classifier.dataset import GEOBOTANY_CLASSES, train_test_split
from models.geobotany_classifier.dataset_sota import _species_to_class


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _inat_json_path() -> Path | None:
    for path in (
        _repo_root() / "data" / "geobotany" / "inaturalist_kenya_plants.json",
        _repo_root() / "tests" / "fixtures" / "inaturalist_kenya_sample.json",
    ):
        if path.exists():
            return path
    return None


def corpus_dir() -> Path:
    return _repo_root() / "data" / "geobotany" / "corpus"


def _observation_key(record: dict[str, Any]) -> str:
    material = (
        f"{record.get('species_guess', '')}:"
        f"{record.get('latitude', '')}:"
        f"{record.get('longitude', '')}:"
        f"{record.get('photo_url', '')}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _image_path_for_record(record: dict[str, Any], class_idx: int) -> Path:
    class_name = GEOBOTANY_CLASSES[class_idx]
    return corpus_dir() / class_name / f"{_observation_key(record)}.jpg"


def render_synthetic_plant_image(
    class_idx: int,
    *,
    seed: int,
    image_size: int = 224,
) -> np.ndarray:
    """Deterministic RGB plant tile when a real iNat photo is unavailable."""

    rng = np.random.default_rng(seed)
    hue = (class_idx * 17 + seed) % 360
    # HSV-ish green foliage with class-specific tint
    r = 0.15 + 0.05 * np.sin(np.deg2rad(hue))
    g = 0.35 + 0.25 * ((class_idx % 7) / 7.0)
    b = 0.10 + 0.08 * np.cos(np.deg2rad(hue * 2))
    base = np.array([r, g, b], dtype=np.float32)
    noise = rng.normal(0.0, 0.06, size=(image_size, image_size, 3)).astype(np.float32)
    texture = rng.uniform(-0.08, 0.08, size=(image_size, image_size, 1)).astype(np.float32)
    image = np.clip(base + noise + texture, 0.0, 1.0)
    return image


def _load_rgb_image(path: Path, *, image_size: int = 224) -> np.ndarray | None:
    if not path.exists():
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    image = Image.open(path).convert("RGB").resize((image_size, image_size))
    return np.asarray(image, dtype=np.float32) / 255.0


def load_observation_records() -> list[dict[str, Any]]:
    path = _inat_json_path()
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("results", []))


def load_image_dataset(
    *,
    image_size: int = 224,
    max_per_class: int | None = None,
    use_synthetic_fallback: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    records = load_observation_records()
    if not records:
        raise FileNotFoundError(
            "No iNaturalist records found; run scripts/datasets/pull_inaturalist.py"
        )

    classes = list(GEOBOTANY_CLASSES)
    images: list[np.ndarray] = []
    labels: list[int] = []
    per_class: dict[int, int] = {}

    for record in records:
        species = record.get("species_guess") or record.get("species")
        class_idx = _species_to_class(species)
        if max_per_class is not None and per_class.get(class_idx, 0) >= max_per_class:
            continue

        image_path = _image_path_for_record(record, class_idx)
        rgb = _load_rgb_image(image_path, image_size=image_size)
        if rgb is None:
            if not use_synthetic_fallback:
                continue
            seed = int(_observation_key(record), 16) % (2**31 - 1)
            rgb = render_synthetic_plant_image(class_idx, seed=seed, image_size=image_size)

        images.append(rgb.transpose(2, 0, 1))  # CHW
        labels.append(class_idx)
        per_class[class_idx] = per_class.get(class_idx, 0) + 1

    if not images:
        raise ValueError("No geobotany images could be loaded")

    x = np.stack(images).astype(np.float32)
    y = np.asarray(labels, dtype=np.int64)
    return x, y, classes


def image_train_test_split(
    x: np.ndarray,
    y: np.ndarray,
    *,
    test_ratio: float = 0.25,
    seed: int = 11,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return train_test_split(x, y, test_ratio=test_ratio, seed=seed)