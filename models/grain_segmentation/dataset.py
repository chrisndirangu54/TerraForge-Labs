from __future__ import annotations

import hashlib

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

IMAGE_SIZE = 64
GRAIN_COUNT = 6


def get_dataset_manifest() -> dict:
    return {
        "source": "MINPET+fixtures",
        "classes": THIN_SECTION_CLASSES,
        "pairs_expected": 20,
        "image_size": IMAGE_SIZE,
    }


def _seed_from_index(index: int, base_seed: int) -> int:
    digest = hashlib.sha256(f"grain:{base_seed}:{index}".encode()).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def generate_synthetic_pair(
    *, index: int = 0, seed: int = 21
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic thin-section image and binary grain mask."""

    rng = np.random.default_rng(_seed_from_index(index, seed))
    image = np.full((IMAGE_SIZE, IMAGE_SIZE), 0.15, dtype=np.float64)
    mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)

    for grain_idx in range(GRAIN_COUNT):
        center_y = int(rng.integers(12, IMAGE_SIZE - 12))
        center_x = int(rng.integers(12, IMAGE_SIZE - 12))
        radius = int(rng.integers(5, 10))
        yy, xx = np.ogrid[:IMAGE_SIZE, :IMAGE_SIZE]
        circle = (yy - center_y) ** 2 + (xx - center_x) ** 2 <= radius**2
        intensity = 0.35 + grain_idx * 0.08
        image[circle] = intensity
        mask[circle] = 1

    noise = rng.normal(0.0, 0.02, size=image.shape)
    image = np.clip(image + noise, 0.0, 1.0)
    return image, mask


def generate_dataset(
    *,
    n_pairs: int = 20,
    seed: int = 21,
) -> tuple[np.ndarray, np.ndarray]:
    images = []
    masks = []
    for index in range(n_pairs):
        image, mask = generate_synthetic_pair(index=index, seed=seed)
        images.append(image)
        masks.append(mask)
    return np.stack(images), np.stack(masks)
