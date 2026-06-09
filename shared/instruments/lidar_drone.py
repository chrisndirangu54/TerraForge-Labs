from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

LIDAR_GROUND_RESOLUTION_M = 0.5
LIDAR_MIN_POINTS_PER_M2 = 4
LIDAR_MAX_FILE_SIZE_GB = 5


@dataclass
class LiDARResult:
    dem_url: str
    dsm_url: str
    chm_url: str
    lineaments_url: str


def parse(filepath: str, crs: str = 'EPSG:4326') -> LiDARResult:
    path = Path(filepath)
    if path.suffix.lower() not in {'.las', '.laz'}:
        raise ValueError('Unsupported LiDAR format; expected .las or .laz')
    stem = path.stem
    return LiDARResult(
        dem_url=f'minio://spectral/{stem}_dem.tif',
        dsm_url=f'minio://spectral/{stem}_dsm.tif',
        chm_url=f'minio://spectral/{stem}_chm.tif',
        lineaments_url=f'minio://spectral/{stem}_lineaments.geojson',
    )
