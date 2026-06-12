from __future__ import annotations

SATELLITE_SOURCES = ["sentinel2", "sar", "grace", "landsat_thermal", "modis_thermal"]


def scene_catalogue(bbox: list[float], start: str, end: str) -> dict:
    return {
        "bbox": bbox,
        "start": start,
        "end": end,
        "scenes": [
            {
                "scene_id": "S2A_MATUU_2026-05-18",
                "source": "sentinel2",
                "date": "2026-05-18",
                "cloud_cover_pct": 8.5,
                "ndvi_mean": 0.42,
                "url": "minio://satellite/sentinel2/latest.tif",
            },
            {
                "scene_id": "S1_MATUU_2026-05-20",
                "source": "sar",
                "date": "2026-05-20",
                "orbit": "ascending",
                "coherence": 0.78,
                "url": "minio://satellite/sar/latest.tif",
            },
            {
                "scene_id": "L8_MATUU_2026-04-02",
                "source": "landsat_thermal",
                "date": "2026-04-02",
                "cloud_cover_pct": 14.2,
                "lst_mean_c": 31.5,
                "url": "minio://satellite/landsat_thermal/latest.tif",
            },
            {
                "scene_id": "MODIS_MATUU_2026-06-01",
                "source": "modis_thermal",
                "date": "2026-06-01",
                "lst_mean_c": 29.8,
                "url": "minio://satellite/modis_thermal/latest.tif",
            },
        ],
        "indices_available": ["ndvi", "ndwi", "iron_oxide", "clay", "lst"],
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
