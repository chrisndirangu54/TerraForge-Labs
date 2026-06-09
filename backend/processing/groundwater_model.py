from __future__ import annotations

import math

THEIS_MIN_DATAPOINTS = 20
WHO_NITRATE_LIMIT_MG_L = 50
WHO_FLUORIDE_LIMIT_MG_L = 1.5
KENYA_NEMA_TDS_LIMIT_MG_L = 1000


def slug_test_conductivity(
    recovery: list[float], casing_radius_m: float = 0.05
) -> dict:
    if len(recovery) < 3:
        raise ValueError("slug test requires at least 3 recovery measurements")
    initial = max(abs(recovery[0]), 0.001)
    final = max(abs(recovery[-1]), 0.001)
    decay = math.log(initial / final) / max(1, len(recovery) - 1)
    hydraulic_conductivity_m_day = max(0.001, decay * casing_radius_m * 864)
    return {
        "method": "cooper_bredehoeft_papadopulos_stub",
        "hydraulic_conductivity_m_day": round(hydraulic_conductivity_m_day, 3),
        "transmissivity_m2_day": round(hydraulic_conductivity_m_day * 10, 3),
    }


def pumping_test_theis(drawdown_m: list[float], pumping_rate_m3_day: float) -> dict:
    if len(drawdown_m) < THEIS_MIN_DATAPOINTS:
        raise ValueError(
            f"pumping test requires at least {THEIS_MIN_DATAPOINTS} points"
        )
    late_drawdown = sum(drawdown_m[-5:]) / 5
    transmissivity = pumping_rate_m3_day / max(0.001, 4 * math.pi * late_drawdown)
    storativity = min(0.3, max(0.0001, late_drawdown / 10_000))
    return {
        "method": "theis_cooper_jacob_stub",
        "transmissivity_m2_day": round(transmissivity, 3),
        "storativity": round(storativity, 6),
        "specific_capacity_m3_day_per_m": round(
            pumping_rate_m3_day / max(late_drawdown, 0.001), 3
        ),
    }


def water_quality_compliance(sample: dict[str, float]) -> dict:
    flags = []
    if sample.get("nitrate_mg_l", 0) > WHO_NITRATE_LIMIT_MG_L:
        flags.append("WHO_NITRATE_EXCEEDANCE")
    if sample.get("fluoride_mg_l", 0) > WHO_FLUORIDE_LIMIT_MG_L:
        flags.append("WHO_FLUORIDE_EXCEEDANCE")
    if sample.get("tds_mg_l", 0) > KENYA_NEMA_TDS_LIMIT_MG_L:
        flags.append("KENYA_NEMA_TDS_EXCEEDANCE")
    return {
        "flags": flags,
        "drinking_water_compliant": not any(flag.startswith("WHO") for flag in flags),
        "nema_compliant": "KENYA_NEMA_TDS_EXCEEDANCE" not in flags,
        "piper_diagram_url": "minio://hydrogeology/piper_diagram.svg",
    }


def build_modflow_model(
    bbox: list[float], recharge_mm_year: float, pumping_wells: int = 0
) -> dict:
    recharge_m_day = recharge_mm_year / 1000 / 365
    converged = recharge_m_day > 0
    return {
        "engine": "MODFLOW 6 via FloPy",
        "bbox": bbox,
        "grid": "structured_or_disv_stub",
        "boundary_conditions": [
            "recharge",
            "general_head",
            "pumping_wells",
            "evapotranspiration",
        ],
        "pumping_wells": pumping_wells,
        "recharge_m_day": round(recharge_m_day, 6),
        "converged": converged,
        "water_table_url": "minio://hydrogeology/water_table.tif",
        "drawdown_map_url": "minio://hydrogeology/drawdown_scenario.tif",
    }


def borehole_siting_report(
    location: dict[str, float], resistivity_ohm_m: float, expected_depth_m: float
) -> dict:
    probability = 0.75 if 20 <= resistivity_ohm_m <= 200 else 0.45
    return {
        "location": location,
        "expected_depth_to_water_m": expected_depth_m,
        "expected_yield_m3_day": round(probability * 120, 1),
        "success_probability": probability,
        "report_url": "minio://reports/borehole_siting_report.pdf",
    }
