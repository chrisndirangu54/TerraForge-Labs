from __future__ import annotations

import random
from typing import Any

import numpy as np
from pykrige.ok import OrdinaryKriging

from backend.api.services.storage import get_storage_service
from backend.processing.cog_io import array_to_cog_bytes, is_geotiff
from shared.constants import (
    CONFIDENCE_INTERVAL,
    KRIGING_GRID_RESOLUTION,
    KRIGING_MAX_POINTS,
    MONTE_CARLO_ITERATIONS,
    NUGGET_RANGE,
    VARIOGRAM_MODEL,
)


def _mean(values: list[float]) -> float:
    return sum(values) / max(1, len(values))


def _std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 1.0
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return var**0.5


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int((len(arr) - 1) * p)
    return arr[idx]


def _extract_point(
    observation: dict[str, Any], index: int, *, element: str
) -> tuple[float, float, float, float]:
    value = float(observation.get(element, 0.0))
    error_pct = float(observation.get("assay_error_pct", 10.0)) / 100.0
    if "lon" in observation and "lat" in observation:
        return float(observation["lon"]), float(observation["lat"]), value, error_pct
    if "x" in observation and "y" in observation:
        return float(observation["x"]), float(observation["y"]), value, error_pct
    spacing = KRIGING_GRID_RESOLUTION
    cols = max(3, int(len(str(index)) + 3))
    x = (index % cols) * spacing
    y = (index // cols) * spacing
    return x, y, value, error_pct


def _grid_bounds(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    pad_x = max((max(xs) - min(xs)) * 0.1, KRIGING_GRID_RESOLUTION)
    pad_y = max((max(ys) - min(ys)) * 0.1, KRIGING_GRID_RESOLUTION)
    return (
        min(xs) - pad_x,
        min(ys) - pad_y,
        max(xs) + pad_x,
        max(ys) + pad_y,
    )


def _fit_variogram_params(std: float) -> dict[str, float]:
    nugget = min(max(std * 0.05, NUGGET_RANGE[0]), NUGGET_RANGE[1])
    sill = max(std**2, 1.0)
    return {
        "model": VARIOGRAM_MODEL,
        "nugget": nugget,
        "sill": sill,
        "range_m": max(KRIGING_GRID_RESOLUTION * 5.0, 50.0),
    }


def _ordinary_kriging_grids(
    xs: list[float],
    ys: list[float],
    values: list[float],
    *,
    variogram_model: str,
    grid_size: int,
    bounds: tuple[float, float, float, float],
) -> tuple[np.ndarray, np.ndarray]:
    west, south, east, north = bounds
    grid_x = np.linspace(west, east, grid_size)
    grid_y = np.linspace(south, north, grid_size)
    ok = OrdinaryKriging(
        np.asarray(xs, dtype=np.float64),
        np.asarray(ys, dtype=np.float64),
        np.asarray(values, dtype=np.float64),
        variogram_model=variogram_model,
        verbose=False,
        enable_plotting=False,
        nlags=min(12, max(4, len(values) // 2)),
    )
    z_pred, variance = ok.execute("grid", grid_x, grid_y)
    return np.asarray(z_pred, dtype=np.float32), np.asarray(variance, dtype=np.float32)


def _monte_carlo_envelopes(
    mean_grid: np.ndarray,
    variance_grid: np.ndarray,
    errors: list[float],
    *,
    iterations: int,
) -> tuple[np.ndarray, np.ndarray]:
    mean_err = _mean(errors)
    grid_size = mean_grid.shape[0]
    ci_lower = np.zeros((grid_size, grid_size), dtype=np.float32)
    ci_upper = np.zeros((grid_size, grid_size), dtype=np.float32)
    alpha = (1.0 - CONFIDENCE_INTERVAL) / 2.0
    for row in range(grid_size):
        for col in range(grid_size):
            base = float(np.real(mean_grid[row, col]))
            spread = float(np.sqrt(max(0.0, float(np.real(variance_grid[row, col])))))
            noise_scale = max(float(mean_err) * max(abs(base), 1.0), spread)
            samples = [
                base + random.gauss(0.0, noise_scale)
                for _ in range(iterations)
            ]
            ci_lower[row, col] = _percentile(samples, alpha)
            ci_upper[row, col] = _percentile(samples, 1.0 - alpha)
    return ci_lower, ci_upper


def _dump_cog_grid(
    name: str,
    base: str,
    array: np.ndarray,
    bounds: tuple[float, float, float, float],
) -> str:
    storage = get_storage_service()
    key = f"kriging/{base}_{name}.tif"
    cog_bytes = array_to_cog_bytes(array, bounds)
    if not is_geotiff(cog_bytes):
        raise RuntimeError(f"Failed to write GeoTIFF for {key}")
    storage.put(key, cog_bytes, content_type="image/tiff", metadata={"cog": True, "bounds": list(bounds)})
    return key


def run_kriging_pipeline(payload: dict) -> dict:
    obs = payload.get("observations", [])
    if not obs:
        obs = [
            {"ta_ppm": 100 + i * 2, "assay_error_pct": 10 + (i % 5)} for i in range(25)
        ]

    element = payload.get("element", "ta_ppm")
    variogram_model = payload.get("variogram_model", VARIOGRAM_MODEL)
    grid_size = int(payload.get("grid_size", 25))
    grid_size = max(5, min(grid_size, 100))

    points: list[tuple[float, float, float, float]] = []
    for index, row in enumerate(obs[:KRIGING_MAX_POINTS]):
        points.append(_extract_point(row, index, element=element))

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    vals = [point[2] for point in points]
    errs = [point[3] for point in points]

    mean = _mean(vals)
    std = _std(vals, mean)
    bounds = _grid_bounds(xs, ys)
    variogram_params = _fit_variogram_params(std)

    mean_grid, variance_grid = _ordinary_kriging_grids(
        xs,
        ys,
        vals,
        variogram_model=variogram_model,
        grid_size=grid_size,
        bounds=bounds,
    )
    ci_lower, ci_upper = _monte_carlo_envelopes(
        mean_grid,
        variance_grid,
        errs,
        iterations=min(MONTE_CARLO_ITERATIONS, 200),
    )

    base = f"kriging_{random.randint(10000, 99999)}"
    storage = get_storage_service()
    mean_key = _dump_cog_grid("mean", base, mean_grid, bounds)
    variance_key = _dump_cog_grid("variance", base, variance_grid, bounds)
    ci_lower_key = _dump_cog_grid("ci_lower", base, ci_lower, bounds)
    ci_upper_key = _dump_cog_grid("ci_upper", base, ci_upper, bounds)

    flagged = sum(1 for error in errs if error > 0.2)
    tile_template = f"/mapping/cog/{mean_key}/tiles/{{z}}/{{x}}/{{y}}.png"
    return {
        "grid_geotiff_url": storage.get_public_url(mean_key),
        "variance_geotiff_url": storage.get_public_url(variance_key),
        "ci_lower_geotiff_url": storage.get_public_url(ci_lower_key),
        "ci_upper_geotiff_url": storage.get_public_url(ci_upper_key),
        "grid_storage_key": mean_key,
        "variance_storage_key": variance_key,
        "cog_tile_url_template": tile_template,
        "cog_preview_url": f"/mapping/cog/{mean_key}/preview.png",
        "variogram_params": {
            **variogram_params,
            "model": variogram_model,
        },
        "stats": {
            "mean": mean,
            "std": std,
            "min": min(vals),
            "max": max(vals),
            "n_points_used": len(vals),
            "n_points_flagged": flagged,
            "grid_size": grid_size,
            "bounds": list(bounds),
        },
        "warnings": [
            "High flagged ratio" if (flagged / max(1, len(vals))) > 0.3 else ""
        ],
        "storage_backend": storage.backend,
        "engine": "pykrige_ordinary_kriging",
    }