from __future__ import annotations

THIN_SECTION_CLASSES = [
    'quartz', 'k_feldspar', 'plagioclase', 'muscovite', 'biotite',
    'hornblende', 'pyroxene', 'olivine', 'calcite', 'coltan', 'ilmenite', 'unknown'
]


def get_dataset_manifest() -> dict:
    return {'source': 'MINPET+fixtures', 'classes': THIN_SECTION_CLASSES, 'pairs_expected': 20}
