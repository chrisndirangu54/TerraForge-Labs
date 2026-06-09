from __future__ import annotations

from pathlib import Path

SUPPORTED_DOWNHOLE_LOGS = [
    "gamma_api",
    "density_g_cm3",
    "sonic_us_ft",
    "resistivity_ohm_m",
    "caliper_mm",
    "deviation_deg",
]


def parse_las(filepath: str | Path) -> list[dict]:
    rows: list[dict] = []
    in_ascii = False
    columns: list[str] = []
    for line in Path(filepath).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith("~A"):
            in_ascii = True
            columns = stripped[2:].split() or [
                "DEPTH",
                "GAMMA",
                "DENSITY",
                "RESISTIVITY",
            ]
            continue
        if in_ascii and not stripped.startswith("#"):
            values = stripped.split()
            if len(values) >= len(columns):
                rows.append(
                    {columns[i].lower(): float(values[i]) for i in range(len(columns))}
                )
    return rows


def correlate_logs_to_lithology(log_rows: list[dict]) -> dict:
    gamma_values = [
        float(row.get("gamma", row.get("gamma_api", 0.0))) for row in log_rows
    ]
    density_values = [
        float(row.get("density", row.get("density_g_cm3", 0.0))) for row in log_rows
    ]
    shale_intervals = sum(1 for value in gamma_values if value > 90)
    massive_intervals = sum(1 for value in density_values if value > 2.8)
    return {
        "row_count": len(log_rows),
        "shale_indicator_intervals": shale_intervals,
        "massive_sulphide_or_mafic_intervals": massive_intervals,
        "correlation_url": "minio://downhole/log_lithology_correlation.csv",
    }
