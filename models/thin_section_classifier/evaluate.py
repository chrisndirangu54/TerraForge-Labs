from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from backend.ml.domain_models import predict_thin_section_cnn, train_thin_section_cnn
from backend.ml.metrics import log_training_run
from backend.ml.stratified_cv import run_stratified_cv
from models.thin_section_classifier.dataset import (
    IMAGE_SIZE,
    generate_dataset,
    load_corpus_dataset,
)

DEFAULT_CHECKPOINT = Path("artifacts/models/thin_section/checkpoint.json")


def evaluate_thin_section_classifier(
    *,
    checkpoint_path: Path | str | None = None,
    data_source: str = "corpus",
    samples_per_class: int = 120,
    seed: int = 19,
    n_splits: int = 5,
    epochs: int = 6,
) -> dict[str, Any]:
    try:
        x, y, classes = load_corpus_dataset()
    except (FileNotFoundError, ValueError):
        x, y, classes = generate_dataset(
            samples_per_class=samples_per_class,
            seed=seed,
        )

    def fit_predict(
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_test: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        checkpoint = train_thin_section_cnn(
            x_train,
            y_train,
            n_classes=len(classes),
            epochs=epochs,
            image_size=IMAGE_SIZE,
        )
        return predict_thin_section_cnn(checkpoint, x_test)

    cv = run_stratified_cv(
        x,
        y,
        n_classes=len(classes),
        n_splits=n_splits,
        seed=seed,
        fit_predict_fn=fit_predict,
    )

    record = log_training_run(
        "thin_section",
        params={
            "evaluation": "stratified_cv",
            "n_splits": cv.get("n_splits", 0),
            "data_source": data_source,
        },
        metrics=cv.get("pooled_metrics", {}),
        artifact_path=str(checkpoint_path or DEFAULT_CHECKPOINT),
        version="thin-section-cv-v1",
        stage="staging",
    )

    return {
        **cv,
        "classes": classes,
        "data_source": data_source,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
        "meets_threshold": cv.get("pooled_metrics", {}).get("accuracy", 0.0) >= 0.70,
        "target_accuracy": 0.70,
    }