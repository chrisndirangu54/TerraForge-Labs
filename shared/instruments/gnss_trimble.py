from __future__ import annotations

from pathlib import Path


class GnssTrimbleParser:
    def parse(self, filepath: str | Path) -> list[dict]:
        rows: list[dict] = []
        for i, line in enumerate(Path(filepath).read_text().splitlines()):
            if not line.startswith("$GPGGA"):
                continue
            parts = line.split(",")
            lat = _nmea_to_decimal(parts[2], parts[3])
            lon = _nmea_to_decimal(parts[4], parts[5])
            fix_q = int(parts[6] or 0)
            hdop = float(parts[8] or 99)
            rows.append(
                {
                    "point_id": f"GNSS-{i:03d}",
                    "lon": lon,
                    "lat": lat,
                    "elevation_m": float(parts[9] or 0),
                    "fix_quality": fix_q,
                    "hdop": hdop,
                    "timestamp": parts[1],
                    "accuracy_m_estimated": 0.02 if fix_q == 5 else (0.5 if fix_q == 4 else 5.0),
                    "flagged": fix_q < 4 or hdop > 2.0,
                }
            )
        return rows


def _nmea_to_decimal(raw: str, hemi: str) -> float:
    if not raw:
        return 0.0
    v = float(raw)
    deg = int(v // 100)
    mins = v - deg * 100
    dec = deg + mins / 60.0
    if hemi in {"S", "W"}:
        dec *= -1
    return dec
