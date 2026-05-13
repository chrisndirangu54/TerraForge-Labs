from pathlib import Path
from typing import Protocol


class ValidationResult(dict):
    pass


class InstrumentParser(Protocol):
    def parse(self, filepath: str | Path): ...

    def validate(self, df) -> ValidationResult: ...

    def to_geojson(self, df, crs: str = "EPSG:4326") -> dict: ...

    def calibrate(self, df, calibration_file: str | None): ...
