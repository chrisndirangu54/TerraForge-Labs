"""Honest holdout evaluation for pretrained_sota mineral and geobotany models."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    f1_scores: list[float] = []
    for class_idx in range(n_classes):
        tp = int(np.sum((y_true == class_idx) & (y_pred == class_idx)))
        fp = int(np.sum((y_true != class_idx) & (y_pred == class_idx)))
        fn = int(np.sum((y_true == class_idx) & (y_pred != class_idx)))
        if tp == 0 and fp == 0 and fn == 0:
            continue
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        if precision + recall == 0:
            continue
        f1_scores.append(2 * precision * recall / (precision + recall))
    return float(np.mean(f1_scores)) if f1_scores else 0.0


def _top_k_accuracy(y_true: np.ndarray, probabilities: np.ndarray, k: int = 3) -> float:
    top_k = np.argsort(probabilities, axis=1)[:, -k:]
    hits = [int(true in row) for true, row in zip(y_true, top_k, strict=False)]
    return float(np.mean(hits))


def _class_distribution(y: np.ndarray, classes: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for idx, name in enumerate(classes):
        counts[name] = int(np.sum(y == idx))
    return {key: value for key, value in counts.items() if value > 0}


def _train_holdout_linear_probe(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    classes: list[str],
    backbone_name: str,
    epochs: int = 12,
    lr: float = 0.05,
) -> tuple[np.ndarray, dict]:
    from backend.ml.pretrained_backbone import (
        build_backbone,
        extract_pretrained_features,
        predict_linear_probe,
        train_linear_probe,
    )

    train_features = extract_pretrained_features(x_train, backbone_name=backbone_name)
    test_features = extract_pretrained_features(x_test, backbone_name=backbone_name)

    checkpoint = train_linear_probe(
        x_train,
        y_train,
        classes=classes,
        backbone_name=backbone_name,
        epochs=epochs,
        lr=lr,
    )
    # Re-fit using only train features (train_linear_probe retrains on passed x — already train only)
    checkpoint["weights"] = checkpoint["weights"]
    train_probs = predict_linear_probe(checkpoint, train_features)
    test_probs = predict_linear_probe(checkpoint, test_features)
    train_pred = np.argmax(train_probs, axis=1)
    test_pred = np.argmax(test_probs, axis=1)

    meta = {
        "backbone": backbone_name,
        "pretrained_weights": checkpoint["pretrained_weights"],
        "epochs": epochs,
        "train_accuracy": float(np.mean(train_pred == y_train)),
        "feature_dim": checkpoint["feature_dim"],
    }
    return test_probs, {
        **meta,
        "test_pred": test_pred,
        "train_pred": train_pred,
    }


def evaluate_task(
    task: str,
    *,
    load_dataset,
    backbone_name: str,
    seed: int,
    test_ratio: float = 0.25,
) -> dict:
    from models.mineral_classifier.dataset import train_test_split as mineral_split
    from models.geobotany_classifier.dataset import train_test_split as geobotany_split

    split_fn = mineral_split if task == "mineral" else geobotany_split
    x, y, classes = load_dataset()
    x_train, x_test, y_train, y_test = split_fn(x, y, test_ratio=test_ratio, seed=seed)

    try:
        test_probs, meta = _train_holdout_linear_probe(
            x_train,
            y_train,
            x_test,
            classes=classes,
            backbone_name=backbone_name,
        )
    except Exception as exc:
        return {
            "task": task,
            "error": str(exc),
            "samples_total": int(len(y)),
            "classes": classes,
        }

    test_pred = meta.pop("test_pred")
    train_pred = meta.pop("train_pred")
    n_classes = len(classes)

    return {
        "task": task,
        "dataset_loader": load_dataset.__module__,
        "backbone": meta["backbone"],
        "pretrained_weights": meta["pretrained_weights"],
        "samples_total": int(len(y)),
        "samples_train": int(len(y_train)),
        "samples_test": int(len(y_test)),
        "classes": len(classes),
        "class_distribution": _class_distribution(y, classes),
        "metrics": {
            "train_accuracy": float(np.mean(train_pred == y_train)),
            "holdout_accuracy": float(np.mean(test_pred == y_test)),
            "holdout_macro_f1": _macro_f1(y_test, test_pred, n_classes),
            "holdout_top3_accuracy": _top_k_accuracy(y_test, test_probs, k=3),
        },
        "per_class_test_support": _class_distribution(y_test, classes),
        "note": (
            "Holdout split is random (not stratified). Small test sets make metrics noisy."
        ),
    }


def main() -> int:
    from models.geobotany_classifier.dataset_real import load_real_dataset as load_geobotany_real
    from models.geobotany_classifier.dataset_sota import load_sota_dataset as load_geobotany_sota
    from models.mineral_classifier.dataset_real import load_real_dataset as load_mineral_real
    from models.mineral_classifier.dataset_sota import load_sota_dataset as load_mineral_sota

    try:
        import torch  # noqa: F401
    except ImportError:
        print(json.dumps({"error": "torch not installed"}, indent=2))
        return 1

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation": "pretrained_sota_holdout",
        "device": "cuda" if __import__("torch").cuda.is_available() else "cpu",
        "tasks": [],
    }

    loaders = [
        ("mineral", "sota_blend", load_mineral_sota, "torchvision-resnet18", 42),
        ("mineral", "real_field", load_mineral_real, "torchvision-resnet18", 43),
        ("geobotany", "sota_blend", load_geobotany_sota, "torchvision-efficientnet-b0", 44),
        ("geobotany", "real_gbif", load_geobotany_real, "torchvision-efficientnet-b0", 45),
    ]

    for task, label, loader, backbone, seed in loaders:
        result = evaluate_task(
            task,
            load_dataset=loader,
            backbone_name=backbone,
            seed=seed,
        )
        result["data_label"] = label
        report["tasks"].append(result)

    out_path = ROOT / "artifacts" / "eval_pretrained_sota_holdout.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())