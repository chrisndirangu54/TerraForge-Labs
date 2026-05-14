from __future__ import annotations

SATELLITE_SOURCES = ["sentinel2", "sar", "grace", "landsat_thermal", "modis_thermal"]


def scene_catalogue(bbox: list[float], start: str, end: str) -> dict:
    return {
        "bbox": bbox,
        "start": start,
        "end": end,
        "scenes": [
            {
                "source": "sentinel2",
                "date": end,
                "cloud_cover_pct": 8.5,
                "url": "minio://satellite/sentinel2/latest.tif",
            },
            {
                "source": "sar",
                "date": end,
                "orbit": "ascending",
                "url": "minio://satellite/sar/latest.tif",
            },
        ],
    }


def latest_index(bbox: list[float], index: str = "ndvi") -> dict:
    return {
        "bbox": bbox,
        "index": index,
        "raster_url": f"minio://satellite/latest_{index}.tif",
        "statistics": {"min": -0.1, "mean": 0.42, "max": 0.91},
    }


def change_detect(before_url: str, after_url: str) -> dict:
    return {
        "method": "multivariate_alteration_detection_stub",
        "before_url": before_url,
        "after_url": after_url,
        "change_raster_url": "minio://satellite/change_detection.tif",
        "changed_area_km2": 2.4,
    }


def insar_request(bbox: list[float], date_range: list[str]) -> dict:
    return {
        "job_id": "insar-phase4-001",
        "bbox": bbox,
        "date_range": date_range,
        "displacement_raster_url": "minio://satellite/insar_displacement.tif",
        "alert_threshold_mm": 15,
    }
