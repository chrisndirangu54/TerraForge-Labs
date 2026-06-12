from __future__ import annotations

from typing import Any

import numpy as np

from backend.ml.domain_models import predict_geobotany_domain_cnn, train_geobotany_domain_cnn
from backend.ml.stratified_cv import run_stratified_cv
from models.geobotany_classifier.dataset_images import load_image_dataset


def evaluate_geobotany_domain_cv(
    *,
    n_splits: int = 3,
    epochs: int = 3,
    seed: int = 19,
    max_per_class: int | None = 8,
) -> dict[str, Any]:
    x, y, classes = load_image_dataset(
        max_per_class=max_per_class,
        use_synthetic_fallback=True,
    )

    def fit_predict(x_train, y_train, x_test):
        checkpoint = train_geobotany_domain_cnn(
            x_train,
            y_train,
            n_classes=len(classes),
            epochs=epochs,
        )
        checkpoint["classes"] = classes
        _pred, probabilities = predict_geobotany_domain_cnn(checkpoint, x_test)
        return probabilities.argmax(axis=1), probabilities

    cv = run_stratified_cv(
        x,
        y,
        n_classes=len(classes),
        n_splits=n_splits,
        seed=seed,
        fit_predict_fn=fit_predict,
    )
    cv["model_type"] = "geobotany_domain_cnn"
    cv["architecture"] = "EfficientNet-B0+domain_head"
    cv["data_source"] = "inat_domain"
    cv["meets_threshold"] = cv["pooled_metrics"].get("accuracy", 0.0) >= 0.80
    return cv