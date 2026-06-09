from __future__ import annotations

STRESS_ZSCORE_THRESHOLD = 2.0
MIN_STRESS_ZONE_AREA_M2 = 300
REP_BLUESHIFT_METAL_NM = 5.0
NDVI_MIN_VEGETATION = 0.20
VII_METAL_STRESS_THRESHOLD = 0.85


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_sentinel_indices(bands: dict[str, float]) -> dict[str, float]:
    """Compute Sentinel-2 vegetation indices used by Track Q.

    Expected keys are Sentinel-2 L2A band names: B02, B03, B04, B05, B06,
    B07, and B08. Missing bands default to zero so API smoke tests can run
    without raster dependencies.
    """

    b02 = bands.get("B02", 0.0)
    b03 = bands.get("B03", 0.0)
    b04 = bands.get("B04", 0.0)
    b05 = bands.get("B05", 0.0)
    b06 = bands.get("B06", 0.0)
    b07 = bands.get("B07", 0.0)
    b08 = bands.get("B08", 0.0)
    ndvi = safe_ratio(b08 - b04, b08 + b04)
    evi = 2.5 * safe_ratio(b08 - b04, b08 + 6 * b04 - 7.5 * b02 + 1)
    ndre = safe_ratio(b06 - b05, b06 + b05)
    cre = safe_ratio(b07, b05) - 1 if b05 else 0.0
    mcari = ((b05 - b04) - 0.2 * (b05 - b03)) * safe_ratio(b05, b04)
    return {
        "ndvi": ndvi,
        "evi": evi,
        "ndre": ndre,
        "cre": cre,
        "mcari": mcari,
    }


def compute_hyperspectral_indices(reflectance_nm: dict[int, float]) -> dict[str, float]:
    """Compute Pika L/Pika IR-L metal-stress indices from reflectance bands."""

    r430 = reflectance_nm.get(430, 0.0)
    r445 = reflectance_nm.get(445, 0.0)
    r550 = reflectance_nm.get(550, 0.0)
    r615 = reflectance_nm.get(615, 0.0)
    r680 = reflectance_nm.get(680, 0.0)
    r700 = reflectance_nm.get(700, 0.0)
    r710 = reflectance_nm.get(710, 0.0)
    r740 = reflectance_nm.get(740, 0.0)
    r760 = reflectance_nm.get(760, 0.0)
    r800 = reflectance_nm.get(800, 0.0)
    red_edge_reference = (r700 + r740) / 2
    red_edge_position = 700 + 40 * safe_ratio(red_edge_reference - r700, r740 - r700)
    return {
        "cu_sri": safe_ratio(r710, r760),
        "npci": safe_ratio(r680 - r430, r680 + r430),
        "sipi": safe_ratio(r800 - r445, r800 - r680),
        "rep_nm": red_edge_position,
        "rep_blueshift_nm": max(0.0, 720.0 - red_edge_position),
        "vii": safe_ratio(r550 + r680, 2 * r615),
    }


def compute_composite_stress(
    indices: dict[str, float],
) -> dict[str, float | bool | str]:
    ndre_component = max(0.0, 1.0 - indices.get("ndre", 0.0)) * 30
    cre_component = max(0.0, 1.0 - indices.get("cre", 0.0)) * 20
    ndvi_component = max(0.0, 1.0 - indices.get("ndvi", 0.0)) * 25
    mcari_component = abs(indices.get("mcari", 0.0)) * 25
    vii_component = max(0.0, indices.get("vii", 0.0) - VII_METAL_STRESS_THRESHOLD) * 25
    rep_component = (
        max(0.0, indices.get("rep_blueshift_nm", 0.0) / REP_BLUESHIFT_METAL_NM) * 25
    )
    score = min(
        100.0,
        ndre_component
        + cre_component
        + ndvi_component
        + mcari_component
        + vii_component
        + rep_component,
    )
    return {
        "composite_stress_score": round(score, 2),
        "flagged": score >= 60
        and indices.get("ndvi", NDVI_MIN_VEGETATION) >= NDVI_MIN_VEGETATION,
        "stress_map_url": "minio://geobotany/vegetation_stress.tif",
        "anomaly_zones_geojson": "minio://geobotany/stress_zones.geojson",
    }


def zscore_anomaly(
    value: float, background_mean: float, background_std: float
) -> dict[str, float | bool]:
    zscore = safe_ratio(value - background_mean, background_std)
    return {"zscore": round(zscore, 3), "flagged": zscore >= STRESS_ZSCORE_THRESHOLD}
