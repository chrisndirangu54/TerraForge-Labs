from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.ml.domain_models import predict_spectral_cnn, train_spectral_cnn
from backend.ml.metrics import log_training_run
from backend.ml.stratified_cv import run_stratified_cv
from models.spectral_classifier.dataset import generate_dataset, load_corpus_dataset

DEFAULT_CHECKPOINT = Path("artifacts/models/spectral/checkpoint.json")


def evaluate_spectral_classifier(
    *,
    checkpoint_path: Path | str | None = None,
    data_source: str = "corpus",
    samples_per_class: int = 200,
    seed: int = 25,
    n_splits: int = 5,
    epochs: int = 8,
) -> dict[str, Any]:
    try:
        x, y, classes = load_corpus_dataset()
    except (FileNotFoundError, ValueError):
        x, y, classes = generate_dataset(samples_per_class=samples_per_class, seed=seed)

    def fit_predict(x_train, y_train, x_test):
        checkpoint = train_spectral_cnn(
            x_train,
            y_train,
            n_classes=len(classes),
            epochs=epochs,
        )
        return predict_spectral_cnn(checkpoint, x_test)

    cv = run_stratified_cv(
        x,
        y,
        n_classes=len(classes),
        n_splits=n_splits,
        seed=seed,
        fit_predict_fn=fit_predict,
    )

    record = log_training_run(
        "spectral",
        params={
            "evaluation": "stratified_cv",
            "n_splits": cv.get("n_splits", 0),
            "data_source": data_source,
        },
        metrics=cv.get("pooled_metrics", {}),
        artifact_path=str(checkpoint_path or DEFAULT_CHECKPOINT),
        version="spectral-cv-v1",
        stage="staging",
    )

    return {
        **cv,
        "classes": classes,
        "data_source": data_source,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
        "meets_threshold": cv.get("pooled_metrics", {}).get("accuracy", 0.0) >= 0.75,
        "target_accuracy": 0.75,
    }