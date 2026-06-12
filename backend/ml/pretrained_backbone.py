from __future__ import annotations

from typing import Any

import numpy as np

from shared.sota_catalog import SOTA_PRETRAINED_MODELS


def torch_available() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


def _geochem_to_rgb_tile(vector: np.ndarray, size: int = 224) -> np.ndarray:
    """Map a geochemical vector to a 3-channel pseudo-image for ImageNet backbones."""

    values = np.asarray(vector, dtype=np.float32).flatten()
    if values.size == 0:
        values = np.zeros(8, dtype=np.float32)
    if values.size < 8:
        values = np.pad(values, (0, 8 - values.size))
    grid = np.tile(values[:8], int(np.ceil((size * size) / 8)))[: size * size]
    grid = (grid - grid.min()) / max(float(grid.max() - grid.min()), 1e-6)
    channel = grid.reshape(size, size)
    rgb = np.stack([channel, np.roll(channel, 3, axis=0), np.roll(channel, 5, axis=1)], axis=0)
    return rgb


def build_backbone(name: str = "torchvision-resnet18"):
    import torch
    import torch.nn as nn
    from torchvision import models

    spec = SOTA_PRETRAINED_MODELS.get(name, SOTA_PRETRAINED_MODELS["torchvision-resnet18"])
    feature_dim = int(spec["feature_dim"])
    if name == "torchvision-efficientnet-b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT
        backbone = models.efficientnet_b0(weights=weights)
        backbone.classifier = nn.Identity()
    else:
        weights = models.ResNet18_Weights.DEFAULT
        backbone = models.resnet18(weights=weights)
        backbone.fc = nn.Identity()
    backbone.eval()
    return backbone, feature_dim, spec


def extract_pretrained_features(
    x: np.ndarray,
    *,
    backbone_name: str = "torchvision-resnet18",
) -> np.ndarray:
    if not torch_available():
        raise RuntimeError("torch is required for pretrained SOTA feature extraction")

    import torch
    from torchvision import transforms

    backbone, _feature_dim, spec = build_backbone(backbone_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    backbone.to(device)

    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    features: list[np.ndarray] = []
    with torch.inference_mode():
        for row in np.asarray(x, dtype=np.float32):
            tile = _geochem_to_rgb_tile(row)
            tensor = transform(tile).unsqueeze(0).to(device)
            embedding = backbone(tensor).detach().float().cpu().numpy()[0]
            features.append(embedding)

    return np.vstack(features)


def train_linear_probe(
    x: np.ndarray,
    y: np.ndarray,
    *,
    classes: list[str],
    backbone_name: str = "torchvision-resnet18",
    epochs: int = 8,
    lr: float = 0.05,
) -> dict[str, Any]:
    if not torch_available():
        raise RuntimeError("torch is required for pretrained SOTA training")

    import torch
    import torch.nn as nn

    features = extract_pretrained_features(x, backbone_name=backbone_name)
    _backbone, feature_dim, spec = build_backbone(backbone_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    x_tensor = torch.tensor(features, dtype=torch.float32, device=device)
    y_tensor = torch.tensor(y, dtype=torch.long, device=device)
    head = nn.Linear(feature_dim, len(classes)).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    head.train()
    for _epoch in range(epochs):
        optimizer.zero_grad()
        logits = head(x_tensor)
        loss = loss_fn(logits, y_tensor)
        loss.backward()
        optimizer.step()

    head.eval()
    with torch.inference_mode():
        logits = head(x_tensor)
        preds = logits.argmax(dim=1).detach().cpu().numpy()
    accuracy = float(np.mean(preds == y))

    return {
        "model_type": "linear_probe_imagenet",
        "backbone": backbone_name,
        "pretrained_weights": spec["weights"],
        "classes": classes,
        "feature_dim": feature_dim,
        "weights": head.weight.detach().cpu().tolist(),
        "bias": head.bias.detach().cpu().tolist(),
        "train_accuracy": accuracy,
        "epochs": epochs,
    }


def predict_linear_probe(checkpoint: dict[str, Any], features: np.ndarray) -> np.ndarray:
    weights = np.asarray(checkpoint["weights"], dtype=np.float64)
    bias = np.asarray(checkpoint["bias"], dtype=np.float64)
    logits = features @ weights.T + bias
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exp / np.maximum(exp.sum(axis=1, keepdims=True), 1e-9)