from __future__ import annotations


def train_grain_segmentation_stub(epochs: int = 2) -> dict:
    loss = 1.0
    history = []
    for _ in range(epochs):
        loss *= 0.78
        history.append(loss)
    return {'history': history, 'mean_iou': 0.75}
