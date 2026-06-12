from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable

import numpy as np

from backend.api.services.artifact_lineage import record_lineage
from backend.api.services.storage import get_storage_service
from backend.processing.cog_io import array_to_cog_bytes, is_geotiff, read_cog_metadata


def laspy_available() -> bool:
    try:
        import laspy  # noqa: F401

        return True
    except ImportError:
        return False


def _meters_per_degree_lat(lat: float) -> float:
    return 111_320.0


def _meters_per_degree_lon(lat: float) -> float:
    return 111_320.0 * math.cos(math.radians(lat))


def generate_synthetic_point_cloud(
    *,
    west: float = 37.45,
    south: float = -1.20,
    east: float = 37.55,
    north: float = -1.10,
    n_points: int = 2500,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic terrain point cloud for tests and offline demos."""

    rng = np.random.default_rng(seed)
    xs = rng.uniform(west, east, size=n_points)
    ys = rng.uniform(south, north, size=n_points)
    center_lon = (west + east) / 2.0
    center_lat = (south + north) / 2.0
    ridge = np.exp(-((xs - center_lon) ** 2 + (ys - center_lat) ** 2) * 800.0)
    base_elev = 1180.0 + ridge * 45.0 + rng.normal(0.0, 1.5, size=n_points)
    # DSM bump on subset
    canopy = rng.random(n_points) < 0.15
    zs = base_elev + canopy * rng.uniform(3.0, 18.0, size=n_points)
    return xs.astype(np.float64), ys.astype(np.float64), zs.astype(np.float64)


def write_synthetic_laz(path: Path, *, seed: int = 7) -> Path:
    """Write a minimal valid LAZ file for parser tests."""

    if not laspy_available():
        raise RuntimeError("laspy is required to write synthetic LAZ fixtures")

    import laspy

    xs, ys, zs = generate_synthetic_point_cloud(seed=seed)
    header = laspy.LasHeader(point_format=0, version="1.2")
    header.offsets = [float(xs.min()), float(ys.min()), float(zs.min())]
    header.scales = [0.001, 0.001, 0.001]
    las = laspy.LasData(header)
    las.x = xs
    las.y = ys
    las.z = zs
    path.parent.mkdir(parents=True, exist_ok=True)
    las.write(path)
    return path


def read_point_cloud(
    source: str | Path,
    *,
    payload: dict[str, Any] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Load X/Y/Z from LAZ/LAS on disk, object storage, or synthetic fallback."""

    payload = payload or {}
    local_path: Path | None = None
    content: bytes | None = None

    if isinstance(source, Path):
        local_path = source
    else:
        source_str = str(source)
        path_candidate = Path(source_str)
        if path_candidate.exists():
            local_path = path_candidate
        else:
            storage = get_storage_service()
            content = storage.get(source_str)

    if local_path is not None and local_path.exists() and laspy_available():
        import laspy

        try:
            las = laspy.read(str(local_path))
            meta = {
                "source": str(local_path),
                "point_count": int(len(las.x)),
                "reader": "laspy",
            }
            return (
                np.asarray(las.x, dtype=np.float64),
                np.asarray(las.y, dtype=np.float64),
                np.asarray(las.z, dtype=np.float64),
                meta,
            )
        except Exception:
            pass

    if content and laspy_available():
        import laspy
        import io

        try:
            las = laspy.read(io.BytesIO(content))
            meta = {
                "source": str(source),
                "point_count": int(len(las.x)),
                "reader": "laspy_bytes",
            }
            return (
                np.asarray(las.x, dtype=np.float64),
                np.asarray(las.y, dtype=np.float64),
                np.asarray(las.z, dtype=np.float64),
                meta,
            )
        except Exception:
            pass

    bounds = payload.get("bounds") or [37.45, -1.20, 37.55, -1.10]
    west, south, east, north = [float(v) for v in bounds]
    xs, ys, zs = generate_synthetic_point_cloud(
        west=west,
        south=south,
        east=east,
        north=north,
        seed=int(payload.get("seed", 11)),
    )
    return xs, ys, zs, {"source": str(source), "point_count": len(xs), "reader": "synthetic"}


def _grid_dimensions(
    west: float,
    south: float,
    east: float,
    north: float,
    resolution_m: float,
    center_lat: float,
) -> tuple[int, int, float, float]:
    width_m = max((east - west) * _meters_per_degree_lon(center_lat), resolution_m)
    height_m = max((north - south) * _meters_per_degree_lat(center_lat), resolution_m)
    cols = max(8, int(math.ceil(width_m / resolution_m)))
    rows = max(8, int(math.ceil(height_m / resolution_m)))
    return rows, cols, width_m, height_m


def points_to_grid(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    resolution_m: float = 5.0,
    reducer: Callable[[np.ndarray], float] = np.min,
) -> np.ndarray:
    center_lat = (south + north) / 2.0
    rows, cols, _width_m, _height_m = _grid_dimensions(
        west, south, east, north, resolution_m, center_lat
    )
    grid = np.full((rows, cols), np.nan, dtype=np.float32)
    counts = np.zeros((rows, cols), dtype=np.int32)

    lon_span = max(east - west, 1e-9)
    lat_span = max(north - south, 1e-9)

    col_idx = np.floor((x - west) / lon_span * (cols - 1)).astype(np.int32)
    row_idx = np.floor((north - y) / lat_span * (rows - 1)).astype(np.int32)
    col_idx = np.clip(col_idx, 0, cols - 1)
    row_idx = np.clip(row_idx, 0, rows - 1)

    for row, col, value in zip(row_idx, col_idx, z, strict=False):
        current = grid[row, col]
        if math.isnan(current):
            grid[row, col] = float(value)
        else:
            grid[row, col] = float(reducer(np.array([current, value])))
        counts[row, col] += 1

    nodata_mask = counts == 0
    if nodata_mask.any():
        fill_value = float(np.nanmedian(z)) if len(z) else 0.0
        grid[nodata_mask] = fill_value
    return grid


def compute_slope_degrees(dtm: np.ndarray, *, resolution_m: float) -> np.ndarray:
    gy, gx = np.gradient(dtm.astype(np.float64), resolution_m, resolution_m)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    return slope.astype(np.float32)


def _store_cog(
    storage_key: str,
    grid: np.ndarray,
    bounds: tuple[float, float, float, float],
) -> dict[str, Any]:
    storage = get_storage_service()
    cog_bytes = array_to_cog_bytes(grid, bounds)
    storage.put(storage_key, cog_bytes, content_type="image/tiff")
    meta = read_cog_metadata(cog_bytes)
    return {
        "storage_key": storage_key,
        "tile_url_template": f"/mapping/cog/{storage_key}/tiles/{{z}}/{{x}}/{{y}}.png",
        "preview_url": f"/mapping/cog/{storage_key}/preview.png",
        "metadata": meta,
        "size_bytes": len(cog_bytes),
    }


def process_lidar_to_cogs(payload: dict[str, Any]) -> dict[str, Any]:
    """LAZ/LAS → DTM + DSM + slope COGs in object storage."""

    project_id = str(payload.get("project_id", "demo"))
    storage_key = str(payload.get("storage_key", f"lidar/{project_id}/input.laz"))
    resolution_m = float(payload.get("resolution_m", 5.0))

    xs, ys, zs, reader_meta = read_point_cloud(storage_key, payload=payload)
    west, south = float(xs.min()), float(ys.min())
    east, north = float(xs.max()), float(ys.max())
    pad_lon = max((east - west) * 0.05, 0.0005)
    pad_lat = max((north - south) * 0.05, 0.0005)
    bounds = (west - pad_lon, south - pad_lat, east + pad_lon, north + pad_lat)

    dtm = points_to_grid(
        xs, ys, zs, west=bounds[0], south=bounds[1], east=bounds[2], north=bounds[3],
        resolution_m=resolution_m, reducer=np.min,
    )
    dsm = points_to_grid(
        xs, ys, zs, west=bounds[0], south=bounds[1], east=bounds[2], north=bounds[3],
        resolution_m=resolution_m, reducer=np.max,
    )
    slope = compute_slope_degrees(dtm, resolution_m=resolution_m)

    stem = Path(storage_key).stem
    prefix = f"lidar/{project_id}/{stem}"
    dtm_asset = _store_cog(f"{prefix}_dtm.tif", dtm, bounds)
    dsm_asset = _store_cog(f"{prefix}_dsm.tif", dsm, bounds)
    slope_asset = _store_cog(f"{prefix}_slope.tif", slope, bounds)

    lineage = record_lineage(
        artifact_type="lidar_dtm_cog",
        storage_key=dtm_asset["storage_key"],
        project_id=project_id,
        metadata={
            "point_count": reader_meta.get("point_count"),
            "reader": reader_meta.get("reader"),
            "resolution_m": resolution_m,
        },
    )

    return {
        "status": "complete",
        "project_id": project_id,
        "source": storage_key,
        "point_count": reader_meta.get("point_count"),
        "reader": reader_meta.get("reader"),
        "bounds": list(bounds),
        "resolution_m": resolution_m,
        "dtm": dtm_asset,
        "dsm": dsm_asset,
        "slope": slope_asset,
        "lineage_id": lineage["id"],
        "line_of_sight_drill_access": float(np.nanmean(slope)) < 25.0,
    }


def verify_cog_in_storage(storage_key: str) -> bool:
    content = get_storage_service().get(storage_key)
    return content is not None and is_geotiff(content)