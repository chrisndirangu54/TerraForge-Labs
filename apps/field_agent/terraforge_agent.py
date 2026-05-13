from __future__ import annotations

AGENT_LOOP_INTERVAL_S = 30
ANOMALY_REPLAN_THRESHOLD = 0.85


def run_agent_cycle(anomaly_score: float, remaining_flight_min: float) -> dict:
    replan = anomaly_score > ANOMALY_REPLAN_THRESHOLD and remaining_flight_min > 15
    return {
        'replan_triggered': replan,
        'reason': 'anomaly threshold crossed' if replan else 'continue mission',
        'mission_kmz_url': 'minio://missions/replanned.kmz' if replan else None,
    }
