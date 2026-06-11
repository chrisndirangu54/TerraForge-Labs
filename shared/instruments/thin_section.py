from __future__ import annotations

from pathlib import Path

from models.grain_segmentation.infer import segment_from_paths

THIN_SECTION_CLASSES = [
    "quartz",
    "k_feldspar",
    "plagioclase",
    "muscovite",
    "biotite",
    "hornblende",
    "pyroxene",
    "olivine",
    "calcite",
    "coltan",
    "ilmenite",
    "unknown",
]


def classify_thin_section(ppl_path: str, xpl_path: str) -> dict:
    if not Path(ppl_path).exists() or not Path(xpl_path).exists():
        raise FileNotFoundError("PPL/XPL file missing")
    return segment_from_paths(ppl_path, xpl_path)
