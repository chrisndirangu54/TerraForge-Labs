from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

TERRAMETER_MAX_RESISTIVITY = 50_000
TERRAMETER_MIN_RESISTIVITY = 0.1
TERRAMETER_IP_NOISE_FLOOR_MS = 0.5


class TerrameterParser:
    def parse(self, filepath: str | Path) -> list[dict]:
        root = ET.parse(filepath).getroot()
        rows: list[dict] = []
        for i, m in enumerate(root.findall(".//measurement")):
            rho = float(m.findtext("apparent_resistivity_ohm_m", "0"))
            spacing = float(m.findtext("electrode_spacing_m", "10"))
            rows.append(
                {
                    "profile_id": m.findtext("profile_id", f"P-{i:02d}"),
                    "electrode_spacing_m": spacing,
                    "apparent_resistivity_ohm_m": rho,
                    "ip_chargeability_ms": float(
                        m.findtext("ip_chargeability_ms", "0")
                    ),
                    "ip_chargeability_ms": float(m.findtext("ip_chargeability_ms", "0")),
                    "sp_mv": float(m.findtext("sp_mv", "0")),
                    "lon": float(m.findtext("lon", "37.5")),
                    "lat": float(m.findtext("lat", "-1.15")),
                    "depth_estimate_m": spacing / 2,
                    "flagged": rho > TERRAMETER_MAX_RESISTIVITY
                    or rho < TERRAMETER_MIN_RESISTIVITY,
                    "flagged": rho > TERRAMETER_MAX_RESISTIVITY or rho < TERRAMETER_MIN_RESISTIVITY,
                }
            )
        return rows

    def invert_1d(self, df: list[dict], n_layers: int = 4) -> list[dict]:
        values = [
            max(r["apparent_resistivity_ohm_m"], TERRAMETER_MIN_RESISTIVITY) for r in df
        ]
        mean_rho = sum(values) / max(1, len(values))
        return [
            {
                "layer": i + 1,
                "resistivity_ohm_m": mean_rho * (1 + i * 0.2),
                "depth_m": (i + 1) * 1.25,
            }
            for i in range(n_layers)
        ]
        values = [max(r["apparent_resistivity_ohm_m"], TERRAMETER_MIN_RESISTIVITY) for r in df]
        mean_rho = sum(values) / max(1, len(values))
        return [{"layer": i + 1, "resistivity_ohm_m": mean_rho * (1 + i * 0.2), "depth_m": (i + 1) * 1.25} for i in range(n_layers)]

    def to_geojson(self, df: list[dict], crs: str = "EPSG:4326") -> dict:
        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": crs}},
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                    "properties": r,
                }
                for r in df
            ],
        }
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]}, "properties": r}
                for r in df
            ],
        }
from shared.instruments._stub_impl import StubParser


class TerrameterParser(StubParser):
    """terrameter parser stub."""
