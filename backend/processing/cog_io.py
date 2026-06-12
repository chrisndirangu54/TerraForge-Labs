from __future__ import annotations

import io
from typing import Any

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds


def _as_float32(array: np.ndarray) -> np.ndarray:
    return np.asarray(array, dtype=np.float32)


def array_to_cog_bytes(
    array: np.ndarray,
    bounds: tuple[float, float, float, float],
    *,
    crs: str = "EPSG:4326",
    nodata: float = -9999.0,
) -> bytes:
    """Write a single-band float grid as a tiled, deflate-compressed GeoTIFF (COG-style)."""

    grid = _as_float32(array)
    grid = np.nan_to_num(grid, nan=nodata, posinf=nodata, neginf=nodata)
    if grid.ndim != 2:
        raise ValueError("array must be 2-dimensional")
    height, width = grid.shape
    west, south, east, north = bounds
    transform = from_bounds(west, south, east, north, width, height)
    profile: dict[str, Any] = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "interleave": "band",
    }
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(grid, 1)
        return memfile.read()


def read_cog_metadata(content: bytes) -> dict[str, Any]:
    with MemoryFile(content) as memfile:
        with memfile.open() as dataset:
            bounds = dataset.bounds
            return {
                "width": dataset.width,
                "height": dataset.height,
                "crs": str(dataset.crs) if dataset.crs else None,
                "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "nodata": dataset.nodata,
                "dtype": str(dataset.dtypes[0]),
            }


def read_cog_array(content: bytes) -> tuple[np.ndarray, dict[str, Any]]:
    with MemoryFile(content) as memfile:
        with memfile.open() as dataset:
            array = dataset.read(1).astype(np.float32)
            bounds = dataset.bounds
            meta = {
                "width": dataset.width,
                "height": dataset.height,
                "crs": str(dataset.crs) if dataset.crs else None,
                "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "transform": dataset.transform,
                "nodata": dataset.nodata,
            }
            return array, meta


def is_geotiff(content: bytes) -> bool:
    if len(content) < 4:
        return False
    if content[:2] == b"II":
        return content[2:4] == b"\x2a\x00"
    if content[:2] == b"MM":
        return content[2:4] == b"\x00\x2a"
    return False


def render_cog_preview_png(content: bytes, *, max_size: int = 256) -> bytes:
    from PIL import Image

    array, meta = read_cog_array(content)
    nodata = meta.get("nodata")
    valid = np.isfinite(array)
    if nodata is not None:
        valid &= array != nodata
    if not valid.any():
        scaled = np.zeros(array.shape, dtype=np.uint8)
    else:
        vmin = float(array[valid].min())
        vmax = float(array[valid].max())
        span = max(vmax - vmin, 1e-6)
        scaled = np.clip((array - vmin) / span * 255.0, 0, 255).astype(np.uint8)
        scaled[~valid] = 0

    image = Image.fromarray(scaled, mode="L")
    image.thumbnail((max_size, max_size), Image.Resampling.BILINEAR)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()