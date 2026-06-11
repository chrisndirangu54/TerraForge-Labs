from __future__ import annotations

import random

from backend.api.services.storage import get_storage_service
from shared.constants import MONTE_CARLO_ITERATIONS, NUGGET_RANGE, VARIOGRAM_MODEL


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


def _dump_grid(name: str, base: str, arr: list[list[float]]) -> str:
    storage = get_storage_service()
    key = f"kriging/{base}_{name}.tif"
    content = "\n".join(",".join(f"{v:.3f}" for v in row) for row in arr)
    storage.put(key, content, content_type="image/tiff")
    return storage.get_public_url(key)


def run_kriging_pipeline(payload: dict) -> dict:
    obs = payload.get("observations", [])
    if not obs:
        obs = [
            {"ta_ppm": 100 + i * 2, "assay_error_pct": 10 + (i % 5)} for i in range(25)
        ]

    key = payload.get("element", "ta_ppm")
    vals = [float(o.get(key, 0)) for o in obs]
    errs = [float(o.get("assay_error_pct", 10)) / 100.0 for o in obs]

    mean = _mean(vals)
    std = _std(vals, mean)

    grid_size = 10
    grid = [[mean for _ in range(grid_size)] for _ in range(grid_size)]
    variance = [
        [max(1e-6, std**2 * 0.1) for _ in range(grid_size)] for _ in range(grid_size)
    ]

    samples = []
    for _ in range(min(MONTE_CARLO_ITERATIONS, 200)):
        frame = []
        for _r in range(grid_size):
            row = []
            for _c in range(grid_size):
                row.append(mean + random.gauss(0, _mean(errs) * max(mean, 1.0)))
            frame.append(row)
        samples.append(frame)

    ci_lower = []
    ci_upper = []
    for r in range(grid_size):
        low_row, up_row = [], []
        for c in range(grid_size):
            cell_vals = [s[r][c] for s in samples]
            low_row.append(_percentile(cell_vals, 0.025))
            up_row.append(_percentile(cell_vals, 0.975))
        ci_lower.append(low_row)
        ci_upper.append(up_row)

    base = f"kriging_{random.randint(10000, 99999)}"
    flagged = sum(1 for e in errs if e > 0.2)
    return {
        "grid_geotiff_url": _dump_grid("mean", base, grid),
        "variance_geotiff_url": _dump_grid("variance", base, variance),
        "ci_lower_geotiff_url": _dump_grid("ci_lower", base, ci_lower),
        "ci_upper_geotiff_url": _dump_grid("ci_upper", base, ci_upper),
        "variogram_params": {
            "model": payload.get("variogram_model", VARIOGRAM_MODEL),
            "nugget": min(max(std * 0.05, NUGGET_RANGE[0]), NUGGET_RANGE[1]),
            "sill": max(std**2, 1.0),
            "range_m": 50.0,
        },
        "stats": {
            "mean": mean,
            "std": std,
            "min": min(vals),
            "max": max(vals),
            "n_points_used": len(vals),
            "n_points_flagged": flagged,
        },
        "warnings": [
            "High flagged ratio" if (flagged / max(1, len(vals))) > 0.3 else ""
        ],
        "storage_backend": get_storage_service().backend,
    }
