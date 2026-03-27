from pathlib import Path
from typing import Protocol

import pandas as pd


class ValidationResult(dict):
    pass


class InstrumentParser(Protocol):
    def parse(self, filepath: str | Path) -> pd.DataFrame: ...

    def validate(self, df: pd.DataFrame) -> ValidationResult: ...

    def to_geojson(self, df: pd.DataFrame, crs: str = "EPSG:4326") -> dict: ...

    def calibrate(self, df: pd.DataFrame, calibration_file: str | None) -> pd.DataFrame: ...
