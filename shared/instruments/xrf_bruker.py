from __future__ import annotations

import csv
import json
import warnings
from pathlib import Path

from shared.instruments.base import ValidationResult

BRUKER_RELEVANT_ELEMENTS = ["Ta", "Nb", "Sn", "W", "Zr", "Hf", "Fe", "Mn", "Ti", "Ce", "La", "Th", "U"]
BRUKER_HIGH_ERROR_THRESHOLD = 0.20
BRUKER_MIN_ACQUISITION_S = 30


class XrfBrukerParser:
    def parse(self, filepath: str | Path, gps_csv: str | None = None) -> list[dict]:
        rows: list[dict] = []
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, r in enumerate(reader):
                ta = float(r.get("Ta_Concentration", 0) or 0)
                nb = float(r.get("Nb_Concentration", 0) or 0)
                ta_err = float(r.get("Ta_Error", 0) or 0)
                acq = float(r.get("Acquisition_Time", 0) or 0)
                lon = float(r.get("lon", 37.5) or 37.5)
                lat = float(r.get("lat", -1.15) or -1.15)
                rel_error = (ta_err / ta) if ta else 0.0
                rows.append(
                    {
                        "sample_id": r.get("Spectrum Label", f"XRF-{i:03d}"),
                        "timestamp": r.get("timestamp", ""),
                        "lon": lon,
                        "lat": lat,
                        "ta_ppm": ta,
                        "nb_ppm": nb,
                        "sn_ppm": float(r.get("Sn_Concentration", 0) or 0),
                        "ta_error_ppm": ta_err,
                        "acquisition_time_s": acq,
                        "method": r.get("Method", "unknown"),
                        "rel_error_pct": rel_error,
                        "flagged": rel_error > BRUKER_HIGH_ERROR_THRESHOLD or acq < BRUKER_MIN_ACQUISITION_S,
                    }
                )
        return rows

    def validate(self, df: list[dict]) -> ValidationResult:
        warnings_list: list[str] = []
        for r in df:
            if r["ta_ppm"] < 0 or r["nb_ppm"] < 0:
                raise ValueError("Negative concentration")
            ta = r["ta_ppm"]
            nb = r["nb_ppm"]
            if ta > 0:
                ratio = nb / ta
                if ratio < 2 or ratio > 20:
                    msg = f"Nb/Ta ratio warning for {r['sample_id']}: {ratio:.2f}"
                    warnings.warn(msg)
                    warnings_list.append(msg)
        return ValidationResult({"valid": True, "warnings": warnings_list, "flagged_count": sum(int(r["flagged"]) for r in df)})

    def calibrate(self, df: list[dict], calibration_file: str | None) -> list[dict]:
        if not calibration_file:
            return df
        cal = json.loads(Path(calibration_file).read_text())
        out = []
        for r in df:
            rr = dict(r)
            for key in ("ta_ppm", "nb_ppm", "sn_ppm"):
                cfg = cal.get(key, {"slope": 1.0, "intercept": 0.0})
                rr[key] = rr[key] * float(cfg.get("slope", 1.0)) + float(cfg.get("intercept", 0.0))
            out.append(rr)
        return out

    def to_geojson(self, df: list[dict], crs: str = "EPSG:4326") -> dict:
        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": crs}},
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                    "properties": {k: v for k, v in r.items() if k not in {"lon", "lat"}},
                }
                for r in df
            ],
        }
