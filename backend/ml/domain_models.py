from __future__ import annotations

from typing import Any

import numpy as np

from backend.ml.stratified_cv import classification_metrics


def torch_available() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


def _require_torch():
    if not torch_available():
        raise RuntimeError("torch is required for domain-specific model training")


class ThinSectionCNN:
    """2-channel (PPL + XPL) thin-section CNN — domain-specific, not ImageNet pseudo-images."""

    def __init__(self, n_classes: int, image_size: int = 128):
        _require_torch()
        import torch.nn as nn

        self.n_classes = n_classes
        self.image_size = image_size
        self.net = nn.Sequential(
            nn.Conv2d(2, 16, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, n_classes),
        )

    def to(self, device):
        self.net = self.net.to(device)
        return self

    def parameters(self):
        return self.net.parameters()

    def train(self):
        self.net.train()

    def eval(self):
        self.net.eval()

    def __call__(self, x):
        return self.net(x)


class Spectral1DCNN:
    """1D CNN on hyperspectral / USGS reflectance vectors."""

    def __init__(self, n_bands: int, n_classes: int):
        _require_torch()
        import torch.nn as nn

        self.n_bands = n_bands
        self.n_classes = n_classes
        self.net = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(16, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(8),
            nn.Flatten(),
            nn.Linear(64 * 8, 96),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(96, n_classes),
        )

    def to(self, device):
        self.net = self.net.to(device)
        return self

    def parameters(self):
        return self.net.parameters()

    def train(self):
        self.net.train()

    def eval(self):
        self.net.eval()

    def __call__(self, x):
        return self.net(x)


def _softmax_numpy(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.maximum(exp.sum(axis=1, keepdims=True), 1e-9)


def train_thin_section_cnn(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    n_classes: int,
    epochs: int = 8,
    batch_size: int = 32,
    lr: float = 1e-3,
    image_size: int = 128,
) -> dict[str, Any]:
    _require_torch()
    import torch
    import torch.nn as nn

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ThinSectionCNN(n_classes=n_classes, image_size=image_size).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    x_tensor = torch.tensor(x_train, dtype=torch.float32, device=device)
    y_tensor = torch.tensor(y_train, dtype=torch.long, device=device)

    model.train()
    for _epoch in range(epochs):
        permutation = torch.randperm(len(y_tensor), device=device)
        for start in range(0, len(y_tensor), batch_size):
            batch_idx = permutation[start : start + batch_size]
            logits = model(x_tensor[batch_idx])
            loss = loss_fn(logits, y_tensor[batch_idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.inference_mode():
        logits = model(x_tensor).detach().cpu().numpy()
    train_pred = logits.argmax(axis=1)
    train_metrics = classification_metrics(
        y_train,
        train_pred,
        _softmax_numpy(logits),
        n_classes=n_classes,
    )

    state = model.net.state_dict()
    return {
        "model_type": "thin_section_cnn",
        "architecture": "ThinSectionCNN",
        "image_size": image_size,
        "n_classes": n_classes,
        "epochs": epochs,
        "state_dict": {key: value.detach().cpu().tolist() for key, value in state.items()},
        "train_metrics": train_metrics,
    }


def predict_thin_section_cnn(
    checkpoint: dict[str, Any],
    x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    _require_torch()
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ThinSectionCNN(
        n_classes=int(checkpoint["n_classes"]),
        image_size=int(checkpoint["image_size"]),
    ).to(device)
    state = {
        key: torch.tensor(value, dtype=torch.float32, device=device)
        for key, value in checkpoint["state_dict"].items()
    }
    model.net.load_state_dict(state)
    model.eval()

    if x.ndim == 3:
        x = x[None, ...]
    x_tensor = torch.tensor(x, dtype=torch.float32, device=device)
    with torch.inference_mode():
        logits = model(x_tensor).detach().cpu().numpy()
    probabilities = _softmax_numpy(logits)
    return probabilities.argmax(axis=1), probabilities


def train_spectral_cnn(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    n_classes: int,
    epochs: int = 10,
    batch_size: int = 64,
    lr: float = 1e-3,
) -> dict[str, Any]:
    _require_torch()
    import torch
    import torch.nn as nn

    n_bands = int(x_train.shape[1])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Spectral1DCNN(n_bands=n_bands, n_classes=n_classes).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    x_tensor = torch.tensor(x_train[:, None, :], dtype=torch.float32, device=device)
    y_tensor = torch.tensor(y_train, dtype=torch.long, device=device)

    model.train()
    for _epoch in range(epochs):
        permutation = torch.randperm(len(y_tensor), device=device)
        for start in range(0, len(y_tensor), batch_size):
            batch_idx = permutation[start : start + batch_size]
            logits = model(x_tensor[batch_idx])
            loss = loss_fn(logits, y_tensor[batch_idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.inference_mode():
        logits = model(x_tensor).detach().cpu().numpy()
    train_pred = logits.argmax(axis=1)
    train_metrics = classification_metrics(
        y_train,
        train_pred,
        _softmax_numpy(logits),
        n_classes=n_classes,
    )

    state = model.net.state_dict()
    return {
        "model_type": "spectral_1d_cnn",
        "architecture": "Spectral1DCNN",
        "n_bands": n_bands,
        "n_classes": n_classes,
        "epochs": epochs,
        "state_dict": {key: value.detach().cpu().tolist() for key, value in state.items()},
        "train_metrics": train_metrics,
    }


def predict_spectral_cnn(
    checkpoint: dict[str, Any],
    x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    _require_torch()
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Spectral1DCNN(
        n_bands=int(checkpoint["n_bands"]),
        n_classes=int(checkpoint["n_classes"]),
    ).to(device)
    state = {
        key: torch.tensor(value, dtype=torch.float32, device=device)
        for key, value in checkpoint["state_dict"].items()
    }
    model.net.load_state_dict(state)
    model.eval()

    if x.ndim == 1:
        x = x.reshape(1, -1)
    x_tensor = torch.tensor(x[:, None, :], dtype=torch.float32, device=device)
    with torch.inference_mode():
        logits = model(x_tensor).detach().cpu().numpy()
    probabilities = _softmax_numpy(logits)
    return probabilities.argmax(axis=1), probabilities