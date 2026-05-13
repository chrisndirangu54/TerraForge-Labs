from __future__ import annotations


def reduce_gravity(_filepath: str) -> dict:
    return {
        'bouguer_anomaly_url': 'minio://seismic/bouguer_map.tif',
        'max_drift_mgal_hr': 0.3,
    }
