from __future__ import annotations


def parse_raman(_filepath: str) -> dict:
    return {
        'peak_table': [
            {'shift_cm_1': 464, 'candidate': 'quartz'},
            {'shift_cm_1': 1008, 'candidate': 'feldspar'},
        ],
        'status': 'phase2_stub',
    }
