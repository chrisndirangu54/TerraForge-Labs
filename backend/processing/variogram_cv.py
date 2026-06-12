from __future__ import annotations

import math
from typing import Any

import numpy as np
from pykrige.ok import OrdinaryKriging


def _euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def empirical_variogram(
    xs: list[float],
    ys: list[float],
    values: list[float],
    *,
    n_lags: int = 10,
) -> dict[str, Any]:
    pairs_h: list[float] = []
    pairs_gamma: list[float] = []
    coords = list(zip(xs, ys, strict=True))
    vals = list(values)
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            dist = _euclidean_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            if dist <= 0:
                continue
            gamma = 0.5 * (vals[i] - vals[j]) ** 2
            pairs_h.append(dist)
            pairs_gamma.append(gamma)

    if not pairs_h:
        return {"lags": [], "semivariance": [], "pairs": 0}

    max_h = max(pairs_h)
    lag_width = max(max_h / n_lags, 1e-6)
    lags: list[float] = []
    semivariance: list[float] = []
    counts: list[int] = []
    for lag_idx in range(n_lags):
        lower = lag_idx * lag_width
        upper = (lag_idx + 1) * lag_width
        bucket = [
            gamma
            for dist, gamma in zip(pairs_h, pairs_gamma, strict=True)
            if lower <= dist < upper or (lag_idx == n_lags - 1 and dist <= upper)
        ]
        if not bucket:
            continue
        lags.append((lower + upper) / 2.0)
        semivariance.append(float(np.mean(bucket)))
        counts.append(len(bucket))

    return {
        "lags": lags,
        "semivariance": semivariance,
        "pair_counts": counts,
        "pairs": len(pairs_h),
        "lag_width": lag_width,
    }


def _model_gamma(h: float, *, model: str, nugget: float, sill: float, range_m: float) -> float:
    if h <= 0:
        return nugget
    hr = h / max(range_m, 1e-9)
    if model == "linear":
        return nugget + sill * min(hr, 1.0)
    if model == "exponential":
        return nugget + sill * (1.0 - math.exp(-3.0 * hr))
    if model == "gaussian":
        return nugget + sill * (1.0 - math.exp(-3.0 * hr * hr))
    # spherical default
    if hr >= 1.0:
        return nugget + sill
    return nugget + sill * (1.5 * hr - 0.5 * hr**3)


def fit_variogram_curve(
    empirical: dict[str, Any],
    *,
    model: str,
    nugget: float,
    sill: float,
    range_m: float,
) -> list[dict[str, float]]:
    lags = empirical.get("lags") or [0.0]
    max_lag = max(lags) if lags else range_m
    samples = np.linspace(0.0, max(max_lag, range_m), max(10, len(lags)))
    return [
        {
            "distance": float(distance),
            "gamma": _model_gamma(
                float(distance),
                model=model,
                nugget=nugget,
                sill=sill,
                range_m=range_m,
            ),
        }
        for distance in samples
    ]


def leave_one_out_cross_validate(
    xs: list[float],
    ys: list[float],
    values: list[float],
    *,
    variogram_model: str = "spherical",
) -> dict[str, Any]:
    n = len(values)
    if n < 4:
        raise ValueError("cross-validation requires at least 4 observations")

    predictions: list[float] = []
    residuals: list[float] = []
    folds: list[dict[str, Any]] = []

    for holdout in range(n):
        train_x = [xs[i] for i in range(n) if i != holdout]
        train_y = [ys[i] for i in range(n) if i != holdout]
        train_z = [values[i] for i in range(n) if i != holdout]
        ok = OrdinaryKriging(
            np.asarray(train_x, dtype=np.float64),
            np.asarray(train_y, dtype=np.float64),
            np.asarray(train_z, dtype=np.float64),
            variogram_model=variogram_model,
            verbose=False,
            enable_plotting=False,
        )
        pred, _var = ok.execute("points", [xs[holdout]], [ys[holdout]])
        predicted = float(pred[0])
        actual = float(values[holdout])
        residual = actual - predicted
        predictions.append(predicted)
        residuals.append(residual)
        folds.append(
            {
                "index": holdout,
                "x": xs[holdout],
                "y": ys[holdout],
                "actual": actual,
                "predicted": predicted,
                "residual": residual,
            }
        )

    abs_errors = [abs(value) for value in residuals]
    sq_errors = [value * value for value in residuals]
    return {
        "method": "leave_one_out",
        "variogram_model": variogram_model,
        "n_folds": n,
        "rmse": float(math.sqrt(sum(sq_errors) / len(sq_errors))),
        "mae": float(sum(abs_errors) / len(abs_errors)),
        "bias": float(sum(residuals) / len(residuals)),
        "folds": folds,
        "predictions": predictions,
        "residuals": residuals,
    }


def analyze_variogram(
    xs: list[float],
    ys: list[float],
    values: list[float],
    *,
    variogram_model: str = "spherical",
    n_lags: int = 10,
) -> dict[str, Any]:
    empirical = empirical_variogram(xs, ys, values, n_lags=n_lags)
    std = float(np.std(values)) if len(values) > 1 else 1.0
    nugget = max(0.05 * std**2, 0.1)
    sill = max(std**2, 1.0)
    span_x = max(max(xs) - min(xs), 1e-6)
    span_y = max(max(ys) - min(ys), 1e-6)
    range_m = max(max(span_x, span_y) * 0.6, 0.01)
    cv = leave_one_out_cross_validate(
        xs, ys, values, variogram_model=variogram_model
    )
    return {
        "empirical": empirical,
        "fitted": {
            "model": variogram_model,
            "nugget": nugget,
            "sill": sill,
            "range_m": range_m,
            "curve": fit_variogram_curve(
                empirical,
                model=variogram_model,
                nugget=nugget,
                sill=sill,
                range_m=range_m,
            ),
        },
        "cross_validation": cv,
    }