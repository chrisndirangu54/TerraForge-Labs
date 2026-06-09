from __future__ import annotations

TRUCK_COST_PER_KM_USD = 1.0
GRID_EXTENSION_COST_USD_PER_KM = 12_000
STARLINK_AVAILABLE_MIN_LAT = -35
STARLINK_AVAILABLE_MAX_LAT = 35


def route_assessment(
    origin: list[float], destination: list[float], distance_km: float
) -> dict:
    return {
        "origin": origin,
        "destination": destination,
        "distance_km": distance_km,
        "travel_time_hours": round(distance_km / 45, 2),
        "haulage_cost_usd": round(distance_km * TRUCK_COST_PER_KM_USD, 2),
        "route_geojson_url": "minio://infrastructure/routes/osrm_route.geojson",
    }


def power_grid_proximity(distance_km: float) -> dict:
    return {
        "nearest_grid_km": distance_km,
        "grid_connection_cost_usd": round(
            distance_km * GRID_EXTENSION_COST_USD_PER_KM, 2
        ),
        "solar_alternative_cost_usd": 280_000,
        "recommendation": "solar_preferred" if distance_km > 20 else "grid_preferred",
    }


def pipeline_route(
    source: list[float], destination: list[float], slope_penalty: float = 1.0
) -> dict:
    length_km = (
        abs(source[0] - destination[0]) * 111 + abs(source[1] - destination[1]) * 111
    )
    cost = length_km * 45_000 * slope_penalty
    return {
        "source": source,
        "destination": destination,
        "length_km": round(length_km, 2),
        "estimated_cost_usd": round(cost, 2),
        "route_geojson_url": "minio://infrastructure/routes/pipeline_least_cost.geojson",
        "constraints": [
            "slope",
            "geology",
            "roads",
            "watercourse_crossings",
            "settlement_buffer",
        ],
    }


def telecoms_coverage(lat: float, nearest_tower_km: float) -> dict:
    starlink_available = STARLINK_AVAILABLE_MIN_LAT <= lat <= STARLINK_AVAILABLE_MAX_LAT
    return {
        "starlink_available": starlink_available,
        "nearest_tower_km": nearest_tower_km,
        "estimated_signal_strength": "good" if nearest_tower_km <= 5 else "weak",
    }


def mining_infrastructure_assessment(payload: dict) -> dict:
    production_tpd = float(payload.get("production_tpd", 500))
    road_km = float(payload.get("nearest_paved_road_km", 12.4))
    grid_km = float(payload.get("nearest_grid_km", 34.2))
    water_demand = production_tpd * 0.5
    groundwater_yield = float(payload.get("groundwater_yield_m3_day", 180))
    road_cost = road_km * 50_000
    power = power_grid_proximity(grid_km)
    total_capex = (
        road_cost
        + power["grid_connection_cost_usd"]
        + max(0, water_demand - groundwater_yield) * 5_000
    )
    return {
        "road_access": {
            "nearest_paved_road_km": road_km,
            "road_upgrade_required": road_km > 5,
            "estimated_road_cost_usd": round(road_cost, 2),
            "route_geojson_url": "minio://infrastructure/road_access.geojson",
        },
        "power": power,
        "water": {
            "groundwater_yield_m3_day": groundwater_yield,
            "processing_water_demand_m3_day": water_demand,
            "deficit_m3_day": max(0, water_demand - groundwater_yield),
        },
        "telecoms": telecoms_coverage(
            float(payload.get("lat", -1.15)),
            float(payload.get("nearest_tower_km", 22.1)),
        ),
        "total_infrastructure_capex_usd": round(total_capex, 2),
        "infrastructure_opex_annual_usd": round(total_capex * 0.08, 2),
        "report_url": "minio://reports/mining_infrastructure_assessment.pdf",
    }
