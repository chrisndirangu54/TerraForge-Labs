from __future__ import annotations


def run_inversion_2d(payload: dict) -> dict:
    return {
        'resistivity_section_url': 'minio://seismic/resistivity_section.tif',
        'depth_to_target_m': 28.4,
        'uncertainty_m': 3.2,
        'input_points': len(payload.get('observations', [])),
    }
