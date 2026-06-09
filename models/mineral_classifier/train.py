from __future__ import annotations

import random


def train_stub(epochs: int = 2, samples: int = 10) -> list[float]:
    random.seed(42)
    loss = 1.0
    history = []
    for _ in range(epochs):
        loss *= 0.8
        history.append(loss)
    return history


if __name__ == "__main__":
    print(train_stub())
