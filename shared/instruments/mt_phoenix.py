from __future__ import annotations


def parse_edi(_filepath: str) -> dict:
    return {
        'resistivity_profile_url': 'minio://seismic/mt_1d_profile.csv',
        'period_range_s': [0.001, 10000],
    }
