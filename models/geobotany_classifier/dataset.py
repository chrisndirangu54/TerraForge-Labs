from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

GEOBOTANY_CLASSES = [
    # Obligate copper indicators
    "ocimum_centraliafricanum",
    "haumaniastrum_katangense",
    "haumaniastrum_robertii",
    "becium_centraliafricanum",
    "aeolanthus_biformifolius",
    "commelina_zigzag",
    # Cobalt indicators
    "silene_cobalticola",
    "crotalaria_cobalticola",
    # Nickel / serpentine
    "senecio_coronatus",
    "pearsonia_metallifera",
    # Geothermal / lithological indicators
    "gypsophila_patrinii",
    "euphorbia_quinquecostata",
    # Lead / zinc and export-market metallophytes
    "minuartia_verna",
    "thlaspi_caerulescens",
    "viola_calaminaria",
    "armeria_maritima",
    # Additional African field targets / negative indicators
    "pityrogramma_calomelanos",
    "equisetum_species",
    "tamarix_species",
    "panicum_maximum",
    # Non-indicator classes
    "healthy_grass",
    "acacia_shrub",
    "miombo_tree",
    "bare_soil",
    "unknown_vegetation",
]

INDICATOR_MINERAL_AFFINITY = {
    "ocimum_centraliafricanum": {"Cu": "VERY_HIGH", "Ni": "HIGH"},
    "haumaniastrum_katangense": {"Cu": "HIGH", "Co": "MEDIUM"},
    "haumaniastrum_robertii": {"Cu": "HIGH", "Co": "HIGH"},
    "becium_centraliafricanum": {"Cu": "HIGH", "Co": "HIGH"},
    "aeolanthus_biformifolius": {"Cu": "HIGH"},
    "commelina_zigzag": {"Cu": "MEDIUM"},
    "silene_cobalticola": {"Co": "VERY_HIGH"},
    "crotalaria_cobalticola": {"Co": "HIGH"},
    "senecio_coronatus": {"Ni": "HIGH", "Cr": "MEDIUM"},
    "pearsonia_metallifera": {"Cu": "HIGH", "Ni": "HIGH"},
    "gypsophila_patrinii": {"B": "MEDIUM", "Li": "MEDIUM"},
    "euphorbia_quinquecostata": {"basement_outcrop": "MEDIUM"},
    "minuartia_verna": {"Pb": "HIGH", "Zn": "HIGH"},
    "thlaspi_caerulescens": {"Zn": "VERY_HIGH", "Cd": "HIGH"},
    "viola_calaminaria": {"Zn": "HIGH"},
    "armeria_maritima": {"Pb": "MEDIUM", "Zn": "MEDIUM"},
    "pityrogramma_calomelanos": {"Au": "MEDIUM", "As": "MEDIUM"},
    "equisetum_species": {"Au": "LOW", "U": "MEDIUM"},
    "tamarix_species": {"B": "MEDIUM", "salinity": "HIGH"},
    "panicum_maximum": {"negative_indicator": "LOW_FERTILITY_OR_DISTURBANCE"},
}

GEOBOTANY_CONFIDENCE_THRESHOLD = 0.65
GEOBOTANY_MODEL_ASSET = "assets/models/geobotany_classifier_int8.tflite"
GEOBOTANY_MODEL_VERSION = "geobotany-b0-v0.1"
TRAINING_DATA_SOURCES = [
    "iNaturalist research-grade observations",
    "GBIF occurrence downloads",
    "East African Plants Database photo guide",
    "TerraForge consented field photos",
]

DEFAULT_FEATURE_DIM = 48
DEFAULT_SAMPLES_PER_CLASS = 24


def get_affinity(species: str) -> dict[str, str]:
    return INDICATOR_MINERAL_AFFINITY.get(species, {})


def _class_seed(class_idx: int, base_seed: int) -> int:
    digest = hashlib.sha256(f"geobotany:{base_seed}:{class_idx}".encode()).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def generate_synthetic_dataset(
    *,
    n_samples_per_class: int = DEFAULT_SAMPLES_PER_CLASS,
    n_features: int = DEFAULT_FEATURE_DIM,
    seed: int = 17,
    noise_std: float = 0.4,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    classes = list(GEOBOTANY_CLASSES)
    rows: list[np.ndarray] = []
    labels: list[int] = []

    for class_idx, _class_name in enumerate(classes):
        rng = np.random.default_rng(_class_seed(class_idx, seed))
        centroid = rng.normal(loc=class_idx * 1.8, scale=0.35, size=n_features)
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
    seed: int = 11,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(y))
    split = max(1, int(len(y) * (1.0 - test_ratio)))
    train_idx = indices[:split]
    test_idx = indices[split:]
    if len(test_idx) == 0:
        test_idx = indices[-1:]
    return x[train_idx], x[test_idx], y[train_idx], y[test_idx]
