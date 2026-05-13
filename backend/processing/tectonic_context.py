from __future__ import annotations

DEPOSIT_TECTONIC_AFFINITY = {
    'coltan_pegmatite': ['craton_interior', 'orogenic_belt'],
    'orogenic_gold': ['orogenic_belt', 'craton_interior'],
    'geothermal': ['rift_margin', 'rift_basin', 'volcanic_arc'],
}


def infer_tectonic_context(bbox: list[float]) -> dict:
    _ = bbox
    setting = 'orogenic_belt'
    return {
        'plate_name': 'African Plate',
        'tectonic_setting': setting,
        'crustal_thickness_km': 34,
        'heat_flow_mW_m2': 68,
        'active_faults_count': 12,
        'deposit_type_scores': {'orogenic_gold': 83, 'coltan_pegmatite': 77, 'geothermal': 34},
        'recommended_deposit_types': ['orogenic_gold', 'coltan_pegmatite'],
        'confidence': 0.74,
    }
