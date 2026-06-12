from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from shared.constants import MINERAL_CLASSES

N_BANDS = 224
WAVELENGTH_MIN_NM = 400
WAVELENGTH_MAX_NM = 2500
DEFAULT_SAMPLES_PER_CLASS = 400
TARGET_CORPUS_SIZE = 3200

SPECTRAL_FEATURE_KEYS = (
    "ta_ppm",
    "nb_ppm",
    "sn_ppm",
    "fe_ppm",
    "reflectance_2200nm",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _usgs_path() -> Path:
    candidates = [
        _repo_root() / "data" / "sota" / "usgs_mineral_signatures.json",
        _repo_root() / "tests" / "fixtures" / "usgs_mineral_signatures.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("USGS mineral signatures missing")


def _manifest_path() -> Path:
    return _repo_root() / "data" / "spectral" / "manifest.json"


def _wavelengths() -> np.ndarray:
    return np.linspace(WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM, N_BANDS, dtype=np.float64)


def _seed(class_idx: int, sample_idx: int, base_seed: int) -> int:
    digest = hashlib.sha256(f"spec:{base_seed}:{class_idx}:{sample_idx}".encode()).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def _base_reflectance_curve(
    *,
    reflectance_2200: float,
    absorption_depth: float,
    absorption_center_nm: float,
    absorption_width_nm: float,
) -> np.ndarray:
    wavelengths = _wavelengths()
    continuum = 0.55 + 0.35 * (1.0 - (wavelengths - WAVELENGTH_MIN_NM) / (WAVELENGTH_MAX_NM - WAVELENGTH_MIN_NM))
    dip = absorption_depth * np.exp(
        -0.5 * ((wavelengths - absorption_center_nm) / max(absorption_width_nm, 1.0)) ** 2
    )
    curve = continuum - dip
    curve += (reflectance_2200 - 0.5) * np.exp(-((wavelengths - 2200.0) / 180.0) ** 2)
    return np.clip(curve, 0.02, 0.99).astype(np.float32)


def _class_spectral_profile(class_name: str) -> dict[str, float]:
    profiles = {
        "coltan": {"reflectance_2200": 0.42, "depth": 0.22, "center": 2200, "width": 90},
        "cassiterite": {"reflectance_2200": 0.38, "depth": 0.18, "center": 1900, "width": 110},
        "quartz": {"reflectance_2200": 0.91, "depth": 0.05, "center": 1400, "width": 70},
        "feldspar": {"reflectance_2200": 0.86, "depth": 0.08, "center": 1550, "width": 80},
        "muscovite": {"reflectance_2200": 0.79, "depth": 0.14, "center": 2208, "width": 75},
        "tourmaline": {"reflectance_2200": 0.55, "depth": 0.16, "center": 2100, "width": 95},
        "ilmenite": {"reflectance_2200": 0.22, "depth": 0.30, "center": 900, "width": 120},
        "unknown": {"reflectance_2200": 0.50, "depth": 0.12, "center": 1800, "width": 100},
    }
    return profiles.get(class_name, profiles["unknown"])


def generate_spectrum(
    *,
    class_idx: int,
    sample_idx: int = 0,
    seed: int = 23,
) -> tuple[np.ndarray, int]:
    class_name = MINERAL_CLASSES[class_idx]
    profile = _class_spectral_profile(class_name)
    rng = np.random.default_rng(_seed(class_idx, sample_idx, seed))
    curve = _base_reflectance_curve(
        reflectance_2200=profile["reflectance_2200"],
        absorption_depth=profile["depth"],
        absorption_center_nm=profile["center"] + rng.normal(0.0, 8.0),
        absorption_width_nm=profile["width"] * (0.9 + rng.random() * 0.2),
    )
    curve += rng.normal(0.0, 0.015, size=curve.shape).astype(np.float32)
    curve = np.clip(curve, 0.01, 0.99)
    return curve, class_idx


def generate_dataset(
    *,
    samples_per_class: int = DEFAULT_SAMPLES_PER_CLASS,
    seed: int = 23,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    spectra: list[np.ndarray] = []
    labels: list[int] = []
    classes = list(MINERAL_CLASSES)
    for class_idx, _name in enumerate(classes):
        for sample_idx in range(samples_per_class):
            curve, label = generate_spectrum(
                class_idx=class_idx,
                sample_idx=sample_idx,
                seed=seed,
            )
            spectra.append(curve)
            labels.append(label)
    x = np.stack(spectra).astype(np.float32)
    y = np.asarray(labels, dtype=np.int64)
    permutation = np.random.default_rng(seed).permutation(len(y))
    return x[permutation], y[permutation], classes


def load_usgs_prototypes() -> dict[str, np.ndarray]:
    payload = json.loads(_usgs_path().read_text(encoding="utf-8"))
    prototypes: dict[str, np.ndarray] = {}
    for mineral, props in (payload.get("minerals") or {}).items():
        profile = _class_spectral_profile(mineral)
        prototypes[mineral] = _base_reflectance_curve(
            reflectance_2200=float(props.get("reflectance_2200nm", profile["reflectance_2200"])),
            absorption_depth=profile["depth"],
            absorption_center_nm=profile["center"],
            absorption_width_nm=profile["width"],
        )
    return prototypes


def load_corpus_dataset(
    *,
    manifest_path: Path | None = None,
    limit: int | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = manifest_path or _manifest_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Spectral manifest missing at {path}; run scripts/datasets/pull_spectral_corpus.py"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    classes = list(payload.get("classes", MINERAL_CLASSES))
    spectra: list[np.ndarray] = []
    labels: list[int] = []
    for record in payload.get("samples", []):
        array_path = _repo_root() / record["array_path"]
        if not array_path.exists():
            continue
        spectra.append(np.load(array_path).astype(np.float32))
        labels.append(int(record["label"]))
        if limit is not None and len(labels) >= limit:
            break
    if not spectra:
        raise ValueError(f"No spectral arrays found for manifest {path}")
    return np.stack(spectra), np.asarray(labels, dtype=np.int64), classes


def get_dataset_manifest() -> dict[str, Any]:
    manifest = _manifest_path()
    if manifest.exists():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "source": payload.get("source", "usgs_spectral_corpus"),
            "classes": payload.get("classes", MINERAL_CLASSES),
            "samples": payload.get("sample_count", 0),
            "n_bands": payload.get("n_bands", N_BANDS),
            "manifest": str(manifest),
        }
    return {
        "source": "usgs_procedural_generator",
        "classes": MINERAL_CLASSES,
        "samples": len(MINERAL_CLASSES) * DEFAULT_SAMPLES_PER_CLASS,
        "n_bands": N_BANDS,
        "manifest": None,
    }