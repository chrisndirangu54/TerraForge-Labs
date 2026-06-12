from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

THIN_SECTION_CLASSES = [
    "quartz",
    "k_feldspar",
    "plagioclase",
    "muscovite",
    "biotite",
    "hornblende",
    "pyroxene",
    "olivine",
    "calcite",
    "coltan",
    "ilmenite",
    "unknown",
]

IMAGE_SIZE = 128
DEFAULT_SAMPLES_PER_CLASS = 200
TARGET_CORPUS_SIZE = 2400


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _corpus_dir() -> Path:
    return _repo_root() / "data" / "thin_section" / "corpus"


def _manifest_path() -> Path:
    return _repo_root() / "data" / "thin_section" / "manifest.json"


def _seed(class_idx: int, sample_idx: int, base_seed: int) -> int:
    digest = hashlib.sha256(f"thin:{base_seed}:{class_idx}:{sample_idx}".encode()).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def _class_optics(class_name: str) -> dict[str, float]:
    optics = {
        "quartz": {"ppl": 0.82, "xpl_amp": 0.05, "grain": 0.9},
        "k_feldspar": {"ppl": 0.74, "xpl_amp": 0.18, "grain": 0.8},
        "plagioclase": {"ppl": 0.70, "xpl_amp": 0.22, "grain": 0.75},
        "muscovite": {"ppl": 0.55, "xpl_amp": 0.35, "grain": 0.6},
        "biotite": {"ppl": 0.35, "xpl_amp": 0.28, "grain": 0.55},
        "hornblende": {"ppl": 0.28, "xpl_amp": 0.20, "grain": 0.5},
        "pyroxene": {"ppl": 0.32, "xpl_amp": 0.24, "grain": 0.52},
        "olivine": {"ppl": 0.48, "xpl_amp": 0.12, "grain": 0.7},
        "calcite": {"ppl": 0.78, "xpl_amp": 0.40, "grain": 0.85},
        "coltan": {"ppl": 0.25, "xpl_amp": 0.08, "grain": 0.45},
        "ilmenite": {"ppl": 0.12, "xpl_amp": 0.04, "grain": 0.4},
        "unknown": {"ppl": 0.50, "xpl_amp": 0.15, "grain": 0.65},
    }
    return optics.get(class_name, optics["unknown"])


def generate_labeled_pair(
    *,
    class_idx: int,
    sample_idx: int = 0,
    seed: int = 17,
    image_size: int = IMAGE_SIZE,
) -> tuple[np.ndarray, int]:
    """Generate a labeled 2-channel PPL/XPL tensor (2, H, W)."""

    class_name = THIN_SECTION_CLASSES[class_idx]
    optics = _class_optics(class_name)
    rng = np.random.default_rng(_seed(class_idx, sample_idx, seed))

    ppl = np.full((image_size, image_size), optics["ppl"], dtype=np.float32)
    xpl = np.full((image_size, image_size), optics["ppl"] * 0.6, dtype=np.float32)

    grain_count = int(rng.integers(4, 9))
    for grain in range(grain_count):
        cy = int(rng.integers(10, image_size - 10))
        cx = int(rng.integers(10, image_size - 10))
        radius = int(rng.integers(6, 14))
        yy, xx = np.ogrid[:image_size, :image_size]
        mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius**2
        intensity = optics["ppl"] * optics["grain"] + grain * 0.02
        ppl[mask] = intensity
        interference = optics["xpl_amp"] * (
            0.5 + 0.5 * np.sin((xx - cx) * 0.35 + grain)
        )
        xpl[mask] = intensity * (0.4 + interference)

    ppl += rng.normal(0.0, 0.03, size=ppl.shape).astype(np.float32)
    xpl += rng.normal(0.0, 0.04, size=xpl.shape).astype(np.float32)
    pair = np.stack(
        [np.clip(ppl, 0.0, 1.0), np.clip(xpl, 0.0, 1.0)],
        axis=0,
    )
    return pair, class_idx


def generate_dataset(
    *,
    samples_per_class: int = DEFAULT_SAMPLES_PER_CLASS,
    seed: int = 17,
    image_size: int = IMAGE_SIZE,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    images: list[np.ndarray] = []
    labels: list[int] = []
    for class_idx, _name in enumerate(THIN_SECTION_CLASSES):
        for sample_idx in range(samples_per_class):
            pair, label = generate_labeled_pair(
                class_idx=class_idx,
                sample_idx=sample_idx,
                seed=seed,
                image_size=image_size,
            )
            images.append(pair)
            labels.append(label)
    x = np.stack(images).astype(np.float32)
    y = np.asarray(labels, dtype=np.int64)
    permutation = np.random.default_rng(seed).permutation(len(y))
    return x[permutation], y[permutation], list(THIN_SECTION_CLASSES)


def load_corpus_dataset(
    *,
    manifest_path: Path | None = None,
    limit: int | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = manifest_path or _manifest_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Thin-section manifest missing at {path}; run scripts/datasets/pull_thin_section_corpus.py"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    classes = list(payload.get("classes", THIN_SECTION_CLASSES))
    images: list[np.ndarray] = []
    labels: list[int] = []
    for record in payload.get("samples", []):
        array_path = _repo_root() / record["array_path"]
        if not array_path.exists():
            continue
        images.append(np.load(array_path).astype(np.float32))
        labels.append(int(record["label"]))
        if limit is not None and len(labels) >= limit:
            break
    if not images:
        raise ValueError(f"No thin-section arrays found for manifest {path}")
    return np.stack(images), np.asarray(labels, dtype=np.int64), classes


def get_dataset_manifest() -> dict[str, Any]:
    manifest = _manifest_path()
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "source": payload.get("source", "terraforge_thin_section_corpus"),
            "classes": payload.get("classes", THIN_SECTION_CLASSES),
            "samples": payload.get("sample_count", 0),
            "image_size": payload.get("image_size", IMAGE_SIZE),
            "manifest": str(manifest),
        }
    return {
        "source": "procedural_generator",
        "classes": THIN_SECTION_CLASSES,
        "samples": len(THIN_SECTION_CLASSES) * DEFAULT_SAMPLES_PER_CLASS,
        "image_size": IMAGE_SIZE,
        "manifest": None,
    }