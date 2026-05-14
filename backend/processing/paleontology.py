from __future__ import annotations


def fossil_occurrences(_bbox: list[float]) -> dict:
    return {
        'type': 'FeatureCollection',
        'features': [
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [36.85, 3.2]}, 'properties': {'taxon': 'Homo sp.', 'age_ma': 1.8}}
        ],
    }


def heritage_risk(_polygon: dict) -> dict:
    return {
        'heritage_risk': 'high',
        'known_localities_within_polygon': 2,
        'recommended_actions': ['Pre-disturbance survey required'],
    }
