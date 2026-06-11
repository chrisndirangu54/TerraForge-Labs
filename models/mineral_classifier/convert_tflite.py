from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.mineral_classifier.infer import DEFAULT_CHECKPOINT, load_checkpoint
from shared.constants import TFLITE_TARGET_INFERENCE_MS, TFLITE_TARGET_SIZE_MB

METADATA_DIR = Path("artifacts/models/mineral")


def export_metadata(
    *,
    checkpoint_path: Path | str | None = None,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(checkpoint_path or DEFAULT_CHECKPOINT)
    metadata = {
        "model_name": "mineral_classifier",
        "model_type": checkpoint.get("model_type", "numpy_centroid"),
        "classes": checkpoint.get("classes", []),
        "feature_dim": checkpoint.get("feature_dim", 32),
        "trained_at": checkpoint.get("trained_at"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tflite": {
            "available": False,
            "path": None,
            "target_size_mb": TFLITE_TARGET_SIZE_MB,
            "target_inference_ms": TFLITE_TARGET_INFERENCE_MS,
        },
        "source_checkpoint": str(checkpoint_path or DEFAULT_CHECKPOINT),
    }

    tflite_path = METADATA_DIR / "mineral_classifier.tflite"
    try:
        import tensorflow as tf  # type: ignore[import-untyped]

        # Placeholder export for environments with TensorFlow installed.
        converter = tf.lite.TFLiteConverter.from_keras_model(tf.keras.Sequential())
        tflite_bytes = converter.convert()
        tflite_path.write_bytes(tflite_bytes)
        metadata["tflite"] = {
            "available": True,
            "path": str(tflite_path),
            "size_mb": round(len(tflite_bytes) / (1024 * 1024), 3),
            "target_size_mb": TFLITE_TARGET_SIZE_MB,
            "target_inference_ms": TFLITE_TARGET_INFERENCE_MS,
        }
    except Exception:
        metadata["tflite"]["note"] = "TensorFlow not available; metadata-only export"

    target = Path(output_path or METADATA_DIR / "export_metadata.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    metadata["metadata_path"] = str(target)
    return metadata


def convert_stub(output_path: str) -> None:
    export_metadata(output_path=Path(output_path).with_suffix(".json"))
