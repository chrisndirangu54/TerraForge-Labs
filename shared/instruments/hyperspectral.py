from __future__ import annotations

from pathlib import Path

SAM_ANGLE_THRESHOLD_RAD = 0.1
MINERAL_MAP_CLASSES = [
    'kaolinite', 'smectite', 'illite', 'jarosite', 'goethite',
    'calcite', 'dolomite', 'quartz', 'feldspar', 'ilmenite', 'unknown'
]


def parse_envi(hdr_path: str, img_path: str) -> dict:
    hdr = Path(hdr_path)
    img = Path(img_path)
    if not hdr.exists() or not img.exists():
        raise FileNotFoundError('Missing ENVI pair (.hdr + .img)')
    return {
        'hdr': str(hdr),
        'img': str(img),
        'bands': 281,
        'classification': 'sam_stub',
        'mineral_map_url': f'minio://spectral/{hdr.stem}_mineral_map.tif',
    }
