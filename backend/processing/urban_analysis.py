from __future__ import annotations

SETTLEMENT_DENSITY_THRESHOLD_PER_HA = 50
UNDERSERVED_DISTANCE_KM = 2.0
FLOOD_RISK_RETURN_PERIOD_YR = 100
MINING_SETTLEMENT_BUFFER_M = 500


def classify_settlement(metrics: dict[str, float]) -> dict:
    density = metrics.get("buildings_per_ha", 0)
    road_density = metrics.get("road_km_per_km2", 0)
    regularity = metrics.get("building_regularity", 0.5)
    if density > 120 and regularity < 0.45:
        label = "informal_settlement"
    elif density >= SETTLEMENT_DENSITY_THRESHOLD_PER_HA and road_density > 8:
        label = "formal_urban"
    elif density >= 15:
        label = "peri_urban"
    elif density >= 3:
        label = "rural_village"
    else:
        label = "dispersed_rural"
    return {"settlement_type": label, "confidence": 0.82, "features": metrics}


def estimate_population(
    building_count: int, floors: float = 1.0, occupancy_rate: float = 3.8
) -> dict:
    population = int(round(building_count * floors * occupancy_rate))
    return {
        "population_estimate": population,
        "method": "worldpop_building_disaggregation_stub",
    }


def service_access(distance_km: float, service_type: str = "water_point") -> dict:
    return {
        "service_type": service_type,
        "distance_km": distance_km,
        "underserved": distance_km > UNDERSERVED_DISTANCE_KM,
        "travel_time_min": round(distance_km / 20 * 60, 1),
    }


def suitability_score(inputs: dict[str, float]) -> dict:
    score = 100
    score -= min(30, inputs.get("distance_to_road_km", 0) * 6)
    score -= min(25, inputs.get("flood_risk", 0) * 25)
    score -= min(20, inputs.get("slope_deg", 0))
    score -= min(15, max(0, 20 - inputs.get("groundwater_depth_m", 20)) * 0.75)
    return {
        "score": round(max(0, score), 2),
        "recommended_land_use": "residential" if score >= 70 else "restricted",
    }


def mining_settlement_conflict(distance_m: float) -> dict:
    return {
        "distance_m": distance_m,
        "conflict": distance_m <= MINING_SETTLEMENT_BUFFER_M,
        "required_action": (
            "community_engagement_required"
            if distance_m <= MINING_SETTLEMENT_BUFFER_M
            else "monitor"
        ),
    }
