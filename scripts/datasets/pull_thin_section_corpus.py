from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from models.thin_section_classifier.dataset import (
    IMAGE_SIZE,
    TARGET_CORPUS_SIZE,
    THIN_SECTION_CLASSES,
    generate_labeled_pair,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pull_thin_section_corpus(
    *,
    samples_per_class: int | None = None,
    seed: int = 17,
) -> dict:
    root = repo_root()
    corpus_dir = root / "data" / "thin_section" / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    per_class = samples_per_class or max(200, TARGET_CORPUS_SIZE // len(THIN_SECTION_CLASSES))
    samples: list[dict] = []

    for class_idx, class_name in enumerate(THIN_SECTION_CLASSES):
        for sample_idx in range(per_class):
            pair, label = generate_labeled_pair(
                class_idx=class_idx,
                sample_idx=sample_idx,
                seed=seed,
            )
            rel_path = Path("data") / "thin_section" / "corpus" / f"{class_name}_{sample_idx:04d}.npy"
            abs_path = root / rel_path
            np.save(abs_path, pair)
            samples.append(
                {
                    "id": f"{class_name}-{sample_idx:04d}",
                    "class_name": class_name,
                    "label": label,
                    "array_path": str(rel_path).replace("\\", "/"),
                    "channels": ["ppl", "xpl"],
                    "image_size": IMAGE_SIZE,
                }
            )

    manifest = {
        "source": "terraforge_procedural_thin_section_corpus",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classes": THIN_SECTION_CLASSES,
        "image_size": IMAGE_SIZE,
        "sample_count": len(samples),
        "samples_per_class": per_class,
        "samples": samples,
        "notes": (
            "Procedural PPL/XPL pairs for domain CNN training. "
            "Replace with MINPET/real thin-section exports as they become available."
        ),
    }
    manifest_path = root / "data" / "thin_section" / "manifest.json"
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
    print(json.dumps(pull_thin_section_corpus(), indent=2))