from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from models.spectral_classifier.dataset import (
    N_BANDS,
    TARGET_CORPUS_SIZE,
    generate_spectrum,
    load_usgs_prototypes,
)
from shared.constants import MINERAL_CLASSES


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pull_spectral_corpus(
    *,
    samples_per_class: int | None = None,
    seed: int = 23,
) -> dict:
    root = repo_root()
    corpus_dir = root / "data" / "spectral" / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    prototypes = load_usgs_prototypes()
    per_class = samples_per_class or max(400, TARGET_CORPUS_SIZE // len(MINERAL_CLASSES))
    samples: list[dict] = []

    for class_idx, class_name in enumerate(MINERAL_CLASSES):
        prototype = prototypes.get(class_name)
        for sample_idx in range(per_class):
            curve, label = generate_spectrum(
                class_idx=class_idx,
                sample_idx=sample_idx,
                seed=seed,
            )
            if prototype is not None and sample_idx % 4 == 0:
                curve = (0.7 * curve + 0.3 * prototype).astype(np.float32)
            rel_path = Path("data") / "spectral" / "corpus" / f"{class_name}_{sample_idx:04d}.npy"
            abs_path = root / rel_path
            np.save(abs_path, curve)
            samples.append(
                {
                    "id": f"{class_name}-{sample_idx:04d}",
                    "class_name": class_name,
                    "label": label,
                    "array_path": str(rel_path).replace("\\", "/"),
                    "n_bands": N_BANDS,
                }
            )

    manifest = {
        "source": "usgs_augmented_spectral_corpus",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classes": MINERAL_CLASSES,
        "n_bands": N_BANDS,
        "sample_count": len(samples),
        "samples_per_class": per_class,
        "usgs_prototypes": list(prototypes.keys()),
        "samples": samples,
        "notes": (
            "USGS-inspired reflectance curves with procedural augmentation. "
            "Swap in ENVI-exported field spectra when available."
        ),
    }
    manifest_path = root / "data" / "spectral" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "status": "ok",
        "sample_count": len(samples),
        "samples_per_class": per_class,
        "manifest": str(manifest_path),
        "corpus_dir": str(corpus_dir),
    }


if __name__ == "__main__":
    print(json.dumps(pull_spectral_corpus(), indent=2))