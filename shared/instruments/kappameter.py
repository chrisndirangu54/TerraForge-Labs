from __future__ import annotations

import csv
from pathlib import Path


class KappameterParser:
    def parse(self, filepath: str | Path) -> list[dict]:
        path = Path(filepath)
        rows: list[dict] = []
        if path.suffix.lower() == ".csv":
            with open(path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    susc = float(r.get("SI_value", 0) or 0)
                    rows.append(
                        {
                            "sample_id": r.get("Index", "SM30"),
                            "susceptibility_si": susc,
                            "temperature_c": float(r.get("Temperature_C", 25) or 25),
                            "timestamp": r.get("Timestamp", ""),
                            "lon": float(r.get("lon", 37.5) or 37.5),
                            "lat": float(r.get("lat", -1.15) or -1.15),
                            "flagged": susc < 0 or susc > 1.0,
                        }
                    )
        else:
            for i, line in enumerate(path.read_text().splitlines()):
                parts = dict(p.split("=") for p in line.split(",") if "=" in p)
                susc = float(parts.get("kappa", "0") or 0)
                rows.append(
                    {
                        "sample_id": f"KT10-{i:03d}",
                        "susceptibility_si": susc,
                        "temperature_c": float(parts.get("temp", "25")),
                        "timestamp": parts.get("ts", ""),
                        "lon": 37.5,
                        "lat": -1.15,
                        "flagged": susc < 0 or susc > 1.0,
                    }
                )
        return rows
