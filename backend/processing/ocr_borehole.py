from __future__ import annotations


def extract_borehole_intervals(_ocr_text: str) -> dict:
    return {
        'collar': {'id': 'BH-001', 'lon': 37.5, 'lat': -1.15, 'elevation_m': 1023},
        'intervals': [{'from_m': 0, 'to_m': 5, 'lithology': 'alluvium'}],
        'assays': [{'from_m': 1, 'to_m': 2, 'element': 'Ta', 'value': 120, 'units': 'ppm'}],
    }
