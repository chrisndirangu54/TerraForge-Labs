from __future__ import annotations

import math

ANOMALY_STRONG_THRESHOLD = 80
ANOMALY_MODERATE_THRESHOLD = 60
GEOBOTANICAL_KRIGING_UNCERTAINTY_FACTOR = 2.5
SPATIAL_JOIN_RADIUS_M = 200

DEFAULT_WEIGHTS = {
    "vegetation_stress": 0.25,
    "indicator_species": 0.30,
    "biogeochemistry": 0.30,
    "species_richness": 0.05,
    "historical_records": 0.10,
}
NO_BIOGEOCHEM_WEIGHTS = {
    "vegetation_stress": 0.35,
    "indicator_species": 0.45,
    "historical_records": 0.20,
}


def composite_anomaly_score(signals: dict[str, float]) -> dict[str, float | str]:
    weights = DEFAULT_WEIGHTS if "biogeochemistry" in signals else NO_BIOGEOCHEM_WEIGHTS
    score = sum(
        float(signals.get(name, 0.0)) * weight for name, weight in weights.items()
    )
    classification = "background"
    if score >= ANOMALY_STRONG_THRESHOLD:
        classification = "strong"
    elif score >= ANOMALY_MODERATE_THRESHOLD:
        classification = "moderate"
    return {
        "score": round(score, 2),
        "classification": classification,
        "anomaly_map_url": "minio://geobotany/composite_anomaly.tif",
        "top_zones_geojson": "minio://geobotany/top_anomaly_zones.geojson",
    }


def pearson_calibration(
    geobotany_scores: list[float], soil_ppm: list[float]
) -> dict[str, float | int]:
    if len(geobotany_scores) != len(soil_ppm) or len(geobotany_scores) < 2:
        return {
            "pairs": min(len(geobotany_scores), len(soil_ppm)),
            "pearson_r": 0.0,
            "r_squared": 0.0,
        }
    mean_geo = sum(geobotany_scores) / len(geobotany_scores)
    mean_soil = sum(soil_ppm) / len(soil_ppm)
    numerator = sum(
        (g - mean_geo) * (s - mean_soil) for g, s in zip(geobotany_scores, soil_ppm)
    )
    geo_var = sum((g - mean_geo) ** 2 for g in geobotany_scores)
    soil_var = sum((s - mean_soil) ** 2 for s in soil_ppm)
    denominator = math.sqrt(geo_var * soil_var)
    pearson_r = numerator / denominator if denominator else 0.0
    return {
        "pairs": len(geobotany_scores),
        "pearson_r": round(pearson_r, 3),
        "r_squared": round(pearson_r**2, 3),
    }


def build_survey_plan(
    bbox: list[float], team_size: int, days: int, priority: str
) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox
    mid_lat = (min_lat + max_lat) / 2
    transects = []
    for idx in range(max(1, days)):
        fraction = (idx + 1) / (days + 1)
        lon = min_lon + (max_lon - min_lon) * fraction
        transects.append(
            {
                "type": "Feature",
                "properties": {
                    "name": f"Track Q transect {idx + 1}",
                    "priority": priority,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, min_lat], [lon, mid_lat], [lon, max_lat]],
                },
            }
        )
    return {
        "transect_plan": {"type": "FeatureCollection", "features": transects},
        "transect_plan_geojson_url": "minio://geobotany/survey_transects.geojson",
        "sampling_protocol_pdf_url": "minio://geobotany/biogeochem_sampling_protocol.pdf",
        "kmz_export_url": "minio://geobotany/survey_transects.kmz",
        "target_species": [
            "ocimum_centraliafricanum",
            "haumaniastrum_katangense",
            "silene_cobalticola",
        ],
        "estimated_observations": max(1, team_size * days * 12),
        "priority": priority,
        "bbox": bbox,
    }
