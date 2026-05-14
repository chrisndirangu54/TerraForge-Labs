from __future__ import annotations

from pathlib import Path

THIN_SECTION_CLASSES = [
    'quartz', 'k_feldspar', 'plagioclase', 'muscovite', 'biotite',
    'hornblende', 'pyroxene', 'olivine', 'calcite', 'coltan', 'ilmenite', 'unknown'
]


def classify_thin_section(ppl_path: str, xpl_path: str) -> dict:
    if not Path(ppl_path).exists() or not Path(xpl_path).exists():
        raise FileNotFoundError('PPL/XPL file missing')
    return {
        'annotated_tiff_url': 'minio://petro/annotated_thin_section.tif',
        'modal_mineralogy': {'quartz': 0.35, 'plagioclase': 0.25, 'coltan': 0.06},
        'status': 'phase2_stub',
    }
