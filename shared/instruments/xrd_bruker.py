from __future__ import annotations

from pathlib import Path

BRUKER_CU_KALPHA_ANGSTROM = 1.5406
XRD_PEAK_MIN_PROMINENCE = 100
XRD_PHASE_MATCH_THRESHOLD = 0.85


def parse_xrd(filepath: str) -> dict:
    path = Path(filepath)
    if path.suffix.lower() not in {'.raw', '.xrdml'}:
        raise ValueError('Unsupported XRD file')
    return {
        'mineral_phases': [
            {'name': 'quartz', 'weight_pct': 42.0, 'match_quality': 0.92},
            {'name': 'feldspar', 'weight_pct': 31.0, 'match_quality': 0.89},
            {'name': 'muscovite', 'weight_pct': 12.0, 'match_quality': 0.86},
        ],
        'diffractogram_url': f'minio://petro/{path.stem}_xrd_curve.csv',
    }
