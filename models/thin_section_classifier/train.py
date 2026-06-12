from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.domain_models import train_thin_section_cnn
from backend.ml.metrics import log_training_run
from backend.ml.stratified_cv import stratified_kfold_indices
from models.thin_section_classifier.dataset import (
    IMAGE_SIZE,
    THIN_SECTION_CLASSES,
    generate_dataset,
    load_corpus_dataset,
)

ARTIFACT_DIR = Path("artifacts/models/thin_section")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = ARTIFACT_DIR / "checkpoint.json"


def _load_training_data(
    *,
    data_source: str,
    samples_per_class: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if data_source in {"corpus", "real"}:
        try:
            return load_corpus_dataset()
        except (FileNotFoundError, ValueError):
            pass
    return generate_dataset(samples_per_class=samples_per_class, seed=seed)


def train_thin_section_classifier(
    *,
    epochs: int = 8,
    samples_per_class: int = 200,
    seed: int = 17,
    data_source: str = "corpus",
    checkpoint_path: Path | None = None,
    use_stratified_holdout: bool = True,
) -> dict[str, Any]:
    x, y, classes = _load_training_data(
        data_source=data_source,
        samples_per_class=samples_per_class,
        seed=seed,
    )

    if use_stratified_holdout:
        folds = stratified_kfold_indices(y, n_splits=5, seed=seed + 1)
        if folds:
            holdout = folds[0]
            x_train, y_train = x[holdout.train_idx], y[holdout.train_idx]
            x_val, y_val = x[holdout.test_idx], y[holdout.test_idx]
        else:
            x_train, y_train = x, y
            x_val, y_val = x[:0], y[:0]
    else:
        x_train, y_train = x, y
        x_val, y_val = x[:0], y[:0]

    checkpoint_body = train_thin_section_cnn(
        x_train,
        y_train,
        n_classes=len(classes),
        epochs=epochs,
        image_size=IMAGE_SIZE,
    )
    checkpoint_body["classes"] = classes
    checkpoint_body["samples"] = int(len(y_train))
    checkpoint_body["data_source"] = data_source
    checkpoint_body["trained_at"] = datetime.now(timezone.utc).isoformat()

    if len(y_val):
        from backend.ml.domain_models import predict_thin_section_cnn
        from backend.ml.stratified_cv import classification_metrics

        val_pred, val_probs = predict_thin_section_cnn(checkpoint_body, x_val)
        checkpoint_body["holdout_metrics"] = classification_metrics(
            y_val,
            val_pred,
            val_probs,
            n_classes=len(classes),
        )

    target = checkpoint_path or CHECKPOINT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(checkpoint_body, indent=2), encoding="utf-8")

    record = log_training_run(
        "thin_section",
        params={
            "architecture": checkpoint_body["architecture"],
            "epochs": epochs,
            "samples": len(y_train),
            "data_source": data_source,
        },
        metrics={
            "train_accuracy": checkpoint_body["train_metrics"]["accuracy"],
            "holdout_accuracy": checkpoint_body.get("holdout_metrics", {}).get("accuracy"),
        },
        artifact_path=str(target),
        stage="staging",
    )
    return {
        "checkpoint_path": str(target),
        "classes": classes,
        "samples": int(len(y)),
        "train_samples": int(len(y_train)),
        "architecture": checkpoint_body["architecture"],
        "data_source": data_source,
        "train_metrics": checkpoint_body["train_metrics"],
        "holdout_metrics": checkpoint_body.get("holdout_metrics"),
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }