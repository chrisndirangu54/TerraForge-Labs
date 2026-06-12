from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

import numpy as np


@dataclass(frozen=True)
class FoldIndices:
    fold: int
    train_idx: np.ndarray
    test_idx: np.ndarray


def stratified_kfold_indices(
    y: np.ndarray,
    *,
    n_splits: int = 5,
    seed: int = 42,
) -> list[FoldIndices]:
    """Yield stratified train/test index arrays for each fold."""

    labels = np.asarray(y, dtype=np.int64)
    if len(labels) == 0:
        return []

    rng = np.random.default_rng(seed)
    folds: list[list[int]] = [[] for _ in range(n_splits)]
    unique_labels = np.unique(labels)

    for label in unique_labels:
        label_idx = np.flatnonzero(labels == label)
        rng.shuffle(label_idx)
        for position, index in enumerate(label_idx):
            folds[position % n_splits].append(int(index))

    result: list[FoldIndices] = []
    all_indices = set(range(len(labels)))
    for fold_id, test_list in enumerate(folds):
        test_idx = np.asarray(sorted(test_list), dtype=np.int64)
        if len(test_idx) == 0:
            continue
        train_idx = np.asarray(
            sorted(all_indices - set(test_idx.tolist())),
            dtype=np.int64,
        )
        if len(train_idx) == 0:
            continue
        result.append(FoldIndices(fold=fold_id, train_idx=train_idx, test_idx=test_idx))
    return result


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    scores: list[float] = []
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
        scores.append(2 * precision * recall / (precision + recall))
    return float(np.mean(scores)) if scores else 0.0


def top_k_accuracy(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    *,
    k: int = 3,
) -> float:
    if len(y_true) == 0:
        return 0.0
    top_k = np.argsort(probabilities, axis=1)[:, -k:]
    hits = [int(true in row) for true, row in zip(y_true, top_k, strict=False)]
    return float(np.mean(hits))


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    probabilities: np.ndarray | None = None,
    *,
    n_classes: int,
) -> dict[str, float]:
    metrics = {
        "accuracy": float(np.mean(y_true == y_pred)) if len(y_true) else 0.0,
        "macro_f1": macro_f1(y_true, y_pred, n_classes),
    }
    if probabilities is not None and len(y_true):
        metrics["top3_accuracy"] = top_k_accuracy(y_true, probabilities, k=3)
    return metrics


def run_stratified_cv(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_classes: int,
    n_splits: int = 5,
    seed: int = 42,
    fit_predict_fn: Callable[
        [np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray | None]
    ],
) -> dict[str, Any]:
    """Run stratified k-fold CV with a caller-provided fit/predict callback."""

    folds = stratified_kfold_indices(y, n_splits=n_splits, seed=seed)
    if not folds:
        return {"error": "insufficient_samples", "n_samples": int(len(y))}

    fold_rows: list[dict[str, Any]] = []
    all_true: list[np.ndarray] = []
    all_pred: list[np.ndarray] = []
    all_probs: list[np.ndarray] = []

    for fold in folds:
        y_pred, probabilities = fit_predict_fn(
            x[fold.train_idx],
            y[fold.train_idx],
            x[fold.test_idx],
        )
        y_test = y[fold.test_idx]
        fold_metrics = classification_metrics(
            y_test,
            y_pred,
            probabilities,
            n_classes=n_classes,
        )
        fold_rows.append(
            {
                "fold": fold.fold,
                "train_samples": int(len(fold.train_idx)),
                "test_samples": int(len(fold.test_idx)),
                "metrics": fold_metrics,
            }
        )
        all_true.append(y_test)
        all_pred.append(y_pred)
        if probabilities is not None:
            all_probs.append(probabilities)

    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_pred)
    pooled_probs = np.concatenate(all_probs) if all_probs else None
    pooled = classification_metrics(
        y_true,
        y_pred,
        pooled_probs,
        n_classes=n_classes,
    )

    def _mean_metric(name: str) -> float:
        values = [row["metrics"][name] for row in fold_rows if name in row["metrics"]]
        return float(np.mean(values)) if values else 0.0

    return {
        "n_splits": len(folds),
        "n_samples": int(len(y)),
        "folds": fold_rows,
        "pooled_metrics": pooled,
        "mean_fold_metrics": {
            "accuracy": _mean_metric("accuracy"),
            "macro_f1": _mean_metric("macro_f1"),
            "top3_accuracy": _mean_metric("top3_accuracy"),
        },
    }


def summarize_metric_list(values: Iterable[float]) -> dict[str, float]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }