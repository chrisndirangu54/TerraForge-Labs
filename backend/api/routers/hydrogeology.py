from __future__ import annotations

from fastapi import APIRouter

from backend.processing.groundwater_model import (
    borehole_siting_report,
    build_modflow_model,
    pumping_test_theis,
    slug_test_conductivity,
    water_quality_compliance,
)

router = APIRouter()


@router.post("/hydro/slug-test")
async def slug_test(payload: dict) -> dict:
    return slug_test_conductivity(
        payload.get("recovery", [1.0, 0.7, 0.45, 0.2]),
        float(payload.get("casing_radius_m", 0.05)),
    )


@router.post("/hydro/pump-test")
async def pump_test(payload: dict) -> dict:
    drawdown = payload.get("drawdown_m", [1 + i * 0.05 for i in range(20)])
    return pumping_test_theis(drawdown, float(payload.get("pumping_rate_m3_day", 250)))


@router.post("/hydro/water-quality")
async def water_quality(payload: dict) -> dict:
    return water_quality_compliance(payload)


@router.post("/hydro/modflow")
async def modflow(payload: dict) -> dict:
    return build_modflow_model(
        payload.get("bbox", [37.45, -1.2, 37.55, -1.1]),
        float(payload.get("recharge_mm_year", 180)),
        int(payload.get("pumping_wells", 0)),
    )


@router.post("/hydro/borehole-siting")
async def borehole_siting(payload: dict) -> dict:
    return borehole_siting_report(
        payload.get("location", {"lon": 37.48, "lat": -1.15}),
        float(payload.get("resistivity_ohm_m", 80)),
        float(payload.get("expected_depth_m", 65)),
    )


@router.get("/hydro/groundwater-table")
async def groundwater_table(bbox: str = "") -> dict:
    return {
        "bbox": bbox,
        "water_table_url": "minio://hydrogeology/water_table_latest.tif",
        "contours_url": "minio://hydrogeology/water_table_contours.geojson",
    }


@router.get("/hydro/boreholes")
async def boreholes(bbox: str = "") -> dict:
    return {
        "bbox": bbox,
        "boreholes": [
            {"id": "BH-MAT-001", "lon": 37.48, "lat": -1.15, "water_level_m": 42.0}
        ],
    }
