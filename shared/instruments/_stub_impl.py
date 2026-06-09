from pathlib import Path

import pandas as pd


class StubParser:
    def parse(self, filepath: str | Path) -> pd.DataFrame:
        return pd.DataFrame([{"source": str(filepath), "value": 0.0}])

    def validate(self, df: pd.DataFrame) -> dict:
        return {"valid": not df.empty, "rows": len(df)}

    def to_geojson(self, df: pd.DataFrame, crs: str = "EPSG:4326") -> dict:
        return {"type": "FeatureCollection", "crs": crs, "features": []}

    def calibrate(self, df: pd.DataFrame, calibration_file: str | None) -> pd.DataFrame:
        calibrated = df.copy()
        calibrated["calibration_file"] = calibration_file or "none"
        return calibrated
