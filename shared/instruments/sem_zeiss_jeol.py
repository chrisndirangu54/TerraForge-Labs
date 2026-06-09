from typing import Protocol, Tuple

import numpy as np

from shared.instruments._stub_impl import StubParser


class SEMParser(Protocol):
    def load_images(self, se_path: str, bse_path: str | None) -> Tuple[np.ndarray, np.ndarray | None]: ...

    def load_eds(self, eds_file: str) -> dict: ...

    def extract_metadata(self, image_path: str) -> dict: ...

    def segment_phases(self, bse_image: np.ndarray) -> np.ndarray: ...

    def quantify_composition(self, eds_data: dict) -> dict: ...


class ZeissJeolSEMParser(StubParser):
    def load_images(self, se_path: str, bse_path: str | None) -> Tuple[np.ndarray, np.ndarray | None]:
        se = np.zeros((64, 64), dtype=np.uint8)
        bse = np.zeros((64, 64), dtype=np.uint8) if bse_path else None
        return se, bse

    def load_eds(self, eds_file: str) -> dict:
        return {"source": eds_file, "elements": {}}

    def extract_metadata(self, image_path: str) -> dict:
        return {"kV": 15.0, "WD_mm": 10.0, "magnification": 1000, "detector": "SE"}

    def segment_phases(self, bse_image: np.ndarray) -> np.ndarray:
        return (bse_image > bse_image.mean()).astype(np.uint8)

    def quantify_composition(self, eds_data: dict) -> dict:
        return {"normalized": True, "data": eds_data}
