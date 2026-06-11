from __future__ import annotations

from backend.ml.metrics import log_training_run


def evaluate_stub() -> dict:
    metrics = {"accuracy": 0.86, "f1_macro": 0.84}
    record = log_training_run(
        "mineral",
        params={"backbone": "torchvision-resnet18", "feature_dim": 512},
        metrics=metrics,
        artifact_path="registry://mineral/eval-stub",
        version="v0.2.0-eval",
        stage="staging",
    )
    return {
        **metrics,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }