from __future__ import annotations

import io
import math
from typing import Any

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import from_bounds as window_from_bounds

from backend.api.services.storage import get_storage_service
from backend.processing.cog_io import render_cog_preview_png


def _tile_bounds_3857(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    n = 2.0**z
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0
    north_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    south_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
    north = math.degrees(north_rad)
    south = math.degrees(south_rad)
    return west, south, east, north


def render_cog_tile_png(
    cog_bytes: bytes,
    *,
    z: int,
    x: int,
    y: int,
    tile_size: int = 256,
) -> bytes:
    from PIL import Image

    west, south, east, north = _tile_bounds_3857(z, x, y)
    with MemoryFile(cog_bytes) as memfile:
        with memfile.open() as src:
            src_crs = src.crs or "EPSG:4326"
            tile_bounds = transform_bounds("EPSG:4326", src_crs, west, south, east, north)
            try:
                window = window_from_bounds(*tile_bounds, transform=src.transform)
                data = src.read(
                    1,
                    window=window,
                    out_shape=(tile_size, tile_size),
                    resampling=Resampling.bilinear,
                    boundless=True,
                    fill_value=src.nodata if src.nodata is not None else -9999,
                ).astype(np.float32)
            except rasterio.errors.WindowError:
                data = np.full((tile_size, tile_size), np.nan, dtype=np.float32)

    valid = np.isfinite(data)
    if src_nodata := (src.nodata if "src" in dir() else None):
        valid &= data != src_nodata
    if not valid.any():
        rgba = np.zeros((tile_size, tile_size, 4), dtype=np.uint8)
    else:
        vmin = float(data[valid].min())
        vmax = float(data[valid].max())
        span = max(vmax - vmin, 1e-6)
        gray = np.clip((data - vmin) / span * 255.0, 0, 255).astype(np.uint8)
        gray[~valid] = 0
        rgba = np.dstack([gray, gray, gray, np.where(valid, 255, 0).astype(np.uint8)])

    image = Image.fromarray(rgba, mode="RGBA")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def get_cog_asset_bytes(storage_key: str) -> bytes | None:
    storage = get_storage_service()
    content = storage.get(storage_key)
    return content


def cog_tile_response(
    storage_key: str,
    *,
    z: int,
    x: int,
    y: int,
) -> tuple[bytes, str]:
    content = get_cog_asset_bytes(storage_key)
    if content is None:
        raise FileNotFoundError(f"COG not found: {storage_key}")
    png = render_cog_tile_png(content, z=z, x=x, y=y)
    return png, "image/png"


def cog_metadata(storage_key: str) -> dict[str, Any]:
    content = get_cog_asset_bytes(storage_key)
    if content is None:
        raise FileNotFoundError(f"COG not found: {storage_key}")
    storage = get_storage_service()
    with MemoryFile(content) as memfile:
        with memfile.open() as dataset:
            bounds = dataset.bounds
            return {
                "storage_key": storage_key,
                "width": dataset.width,
                "height": dataset.height,
                "crs": str(dataset.crs) if dataset.crs else None,
                "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "tile_url_template": (
                    f"/mapping/cog/{storage_key}/tiles/{{z}}/{{x}}/{{y}}.png"
                ),
                "preview_url": f"/mapping/cog/{storage_key}/preview.png",
                "artifact_url": storage.get_public_url(storage_key),
                "artifact_signed_url": storage.get_signed_url(storage_key),
            }


def cog_preview(storage_key: str) -> tuple[bytes, str]:
    content = get_cog_asset_bytes(storage_key)
    if content is None:
        raise FileNotFoundError(f"COG not found: {storage_key}")
    return render_cog_preview_png(content), "image/png"