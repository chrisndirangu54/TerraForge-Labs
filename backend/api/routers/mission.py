from __future__ import annotations

from fastapi import APIRouter

from apps.field_agent.terraforge_agent import run_agent_cycle

router = APIRouter()


@router.post('/plan-mission')
async def plan_mission(payload: dict) -> dict:
    cycle = run_agent_cycle(payload.get('anomaly_score', 0.1), payload.get('remaining_flight_min', 60))
    return {
        'mission_kmz_url': cycle.get('mission_kmz_url') or 'minio://missions/default_plan.kmz',
        'flight_lines_geojson_url': 'minio://missions/flight_lines.geojson',
        'estimated_coverage_km2': 8.4,
        'estimated_flight_time_min': 47,
        'n_battery_swaps': 1,
    }
