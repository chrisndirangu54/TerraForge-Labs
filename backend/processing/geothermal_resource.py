from __future__ import annotations


def estimate_geothermal_resource(reservoir_volume_km3: float, mean_temp_c: float) -> dict:
    heat_in_place_pj = reservoir_volume_km3 * max(mean_temp_c - 25, 0) * 2.5
    recoverable_pj = heat_in_place_pj * 0.25
    electrical_potential_mwe = recoverable_pj * 0.12
    return {
        'reservoir_volume_km3': reservoir_volume_km3,
        'mean_temp_c': mean_temp_c,
        'heat_in_place_PJ': round(heat_in_place_pj, 2),
        'recoverable_PJ': round(recoverable_pj, 2),
        'electrical_potential_MWe': round(electrical_potential_mwe, 2),
        'confidence': 'inferred',
    }
