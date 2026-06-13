from __future__ import annotations

import csv
import math
from pathlib import Path

from backend.api.services.storage import get_storage_service
from shared.constants import (
    GEMPY_DEPTH_EXTENT_M,
    GEMPY_RESOLUTION,
    TA_GRADE_THRESHOLD_PPM,
)

MATUU_CENTRE_LON = 37.5
MATUU_CENTRE_LAT = -1.15
MATUU_SURFACE_ELEVATION_M = 1180.0
BLOCK_SPACING_DEG = 0.0012
BLOCK_SIZE_M = 50.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


ARTIFACT_DIR = _repo_root() / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def block_geo_coords(index: int, grid_width: int = 5) -> dict[str, float]:
    row = index // grid_width
    col = index % grid_width
    lon = MATUU_CENTRE_LON + (col - grid_width / 2) * BLOCK_SPACING_DEG
    lat = MATUU_CENTRE_LAT + (row - grid_width / 2) * BLOCK_SPACING_DEG
    depth_m = (index % 5) * 25.0
    elevation_m = MATUU_SURFACE_ELEVATION_M - depth_m
    return {
        "lon": round(lon, 6),
        "lat": round(lat, 6),
        "elevation_m": round(elevation_m, 1),
        "depth_m": round(depth_m, 1),
    }


def grade_color_hex(grade: float) -> str:
    ratio = min(max((grade - 80.0) / 120.0, 0.0), 1.0)
    red = int(80 + ratio * 175)
    green = int(40 + (1.0 - ratio) * 80)
    blue = int(30 + (1.0 - ratio) * 40)
    return f"#{red:02x}{green:02x}{blue:02x}"


def generate_deposit_model_files(payload: dict) -> dict:
    base = payload.get("job_id", "deposit_model")
    obj_path = ARTIFACT_DIR / f"{base}.obj"
    csv_path = ARTIFACT_DIR / f"{base}_block_model.csv"
    prob_path = ARTIFACT_DIR / f"{base}_probability.tif"

    vertices: list[str] = []
    faces: list[str] = []
    vertex_offset = 1

    fieldnames = [
        "x",
        "y",
        "z",
        "lon",
        "lat",
        "elevation_m",
        "depth_m",
        "ta_ppm_mean",
        "ta_ppm_p10",
        "ta_ppm_p90",
        "unit",
        "color_hex",
    ]

    rows: list[dict[str, float | str]] = []
    for i in range(20):
        geo = block_geo_coords(i)
        grade = 120.0 + i * 3.5
        row = {
            "x": float(i % 5),
            "y": float(i // 5),
            "z": float(i % 5),
            **geo,
            "ta_ppm_mean": round(grade, 2),
            "ta_ppm_p10": round(grade - 20.0, 2),
            "ta_ppm_p90": round(grade + 25.0, 2),
            "unit": "pegmatite" if i % 2 == 0 else "saprolite",
            "color_hex": grade_color_hex(grade),
        }
        rows.append(row)

        half = BLOCK_SIZE_M / 2.0
        # East-North-Up metres relative to deposit centre (Cesium ENU frame).
        east = (geo["lon"] - MATUU_CENTRE_LON) * 111_320.0 * max(
            0.2, abs(math.cos(math.radians(MATUU_CENTRE_LAT)))
        )
        north = (geo["lat"] - MATUU_CENTRE_LAT) * 111_320.0
        up = geo["elevation_m"] - MATUU_SURFACE_ELEVATION_M
        cube = [
            (east - half, north - half, up - half),
            (east + half, north - half, up - half),
            (east + half, north + half, up - half),
            (east - half, north + half, up - half),
            (east - half, north - half, up + half),
            (east + half, north - half, up + half),
            (east + half, north + half, up + half),
            (east - half, north + half, up + half),
        ]
        for vx, vy, vz in cube:
            vertices.append(f"v {vx:.2f} {vy:.2f} {vz:.2f}")
        faces.extend(
            [
                f"f {vertex_offset} {vertex_offset + 1} {vertex_offset + 2} {vertex_offset + 3}",
                f"f {vertex_offset + 4} {vertex_offset + 5} {vertex_offset + 6} {vertex_offset + 7}",
                f"f {vertex_offset} {vertex_offset + 1} {vertex_offset + 5} {vertex_offset + 4}",
                f"f {vertex_offset + 2} {vertex_offset + 3} {vertex_offset + 7} {vertex_offset + 6}",
                f"f {vertex_offset} {vertex_offset + 3} {vertex_offset + 7} {vertex_offset + 4}",
                f"f {vertex_offset + 1} {vertex_offset + 2} {vertex_offset + 6} {vertex_offset + 5}",
            ]
        )
        vertex_offset += 8

    obj_path.write_text(
        "\n".join(["o TerraforgeDeposit", *vertices, *faces]),
        encoding="utf-8",
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    prob_path.write_text("probability-grid-placeholder", encoding="utf-8")

    storage = get_storage_service()
    obj_key = f"models/{obj_path.name}"
    csv_key = f"models/{csv_path.name}"
    prob_key = f"models/{prob_path.name}"
    storage.put(obj_key, obj_path.read_bytes(), content_type="model/obj")
    storage.put(csv_key, csv_path.read_bytes(), content_type="text/csv")
    storage.put(prob_key, prob_path.read_bytes(), content_type="image/tiff")

    grades = [float(row["ta_ppm_mean"]) for row in rows]
    mean_grade = sum(grades) / len(grades)
    block_volume_m3 = len(rows) * (BLOCK_SIZE_M ** 3)
    ore_tonnes = block_volume_m3 * 2.7

    return {
        "mesh_url": f"/deposit/mesh?base={base}",
        "block_model_url": storage.get_signed_url(csv_key),
        "probability_map_url": storage.get_signed_url(prob_key),
        "mesh_storage_key": obj_key,
        "block_model_storage_key": csv_key,
        "blocks_preview": rows[:24],
        "summary": {
            "estimated_deposit_volume_m3": round(block_volume_m3, 1),
            "mean_grade_ta_ppm": round(mean_grade, 2),
            "resource_category": "inferred",
            "resolution": GEMPY_RESOLUTION,
            "depth_extent_m": GEMPY_DEPTH_EXTENT_M,
            "ta_grade_threshold_ppm": TA_GRADE_THRESHOLD_PPM,
            "block_count": len(rows),
            "ore_tonnes_estimate": round(ore_tonnes, 0),
            "centre": {
                "lon": MATUU_CENTRE_LON,
                "lat": MATUU_CENTRE_LAT,
                "elevation_m": MATUU_SURFACE_ELEVATION_M,
            },
        },
    }