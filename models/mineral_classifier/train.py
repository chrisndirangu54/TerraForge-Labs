from __future__ import annotations

import random

from backend.ml.metrics import log_training_run


def train_stub(epochs: int = 2, samples: int = 10) -> dict:
    random.seed(42)
    loss = 1.0
    history = []
    for _ in range(epochs):
        loss *= 0.8
        history.append(loss)

    final_loss = history[-1] if history else loss
    record = log_training_run(
        "mineral",
        params={
            "epochs": epochs,
            "samples": samples,
            "backbone": "torchvision-resnet18",
            "feature_dim": 512,
        },
        metrics={"train_loss": final_loss},
        artifact_path="registry://mineral/train-stub",
        stage="staging",
    )
    return {
        "history": history,
        "version": record["version"],
        "stage": record["stage"],
        "artifact_path": record["artifact_path"],
    }


if __name__ == "__main__":
    print(train_stub())