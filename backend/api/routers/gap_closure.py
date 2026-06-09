from __future__ import annotations

from fastapi import APIRouter

from backend.processing.gap_closure import (
    dispersion_model,
    earth_observation_correction,
    ert_3d_inversion,
    flood_inundation_model,
    fluid_inclusion_summary,
    geochemistry_qaqc,
    groundwater_age,
    investor_data_room,
    lims_sample_event,
    modpath_capture_zone,
    optimise_drill_plan,
    pathfinder_analysis,
    sequential_gaussian_simulation,
    soil_gas_interpretation,
    structural_assessment,
    tenement_obligations,
    traffic_haulage_simulation,
)

router = APIRouter()


@router.post("/targeting/pathfinder-analysis")
async def targeting_pathfinder(payload: dict) -> dict:
    return pathfinder_analysis(
        payload.get("samples", []), payload.get("deposit_style", "orogenic_au")
    )


@router.post("/targeting/drill-plan-optimise")
async def targeting_drill_plan(payload: dict) -> dict:
    return optimise_drill_plan(
        payload.get("targets", []),
        float(payload.get("budget_usd", 50_000)),
        float(payload.get("max_depth_m", 250)),
    )


@router.post("/targeting/geostat-simulate")
async def targeting_geostat_simulate(payload: dict) -> dict:
    return sequential_gaussian_simulation(
        payload.get("samples", []), int(payload.get("realisations", 100))
    )


@router.post("/geochemistry/soil-gas")
async def geochemistry_soil_gas(payload: dict) -> dict:
    return soil_gas_interpretation(payload.get("readings", []))


@router.post("/geochemistry/qaqc")
async def geochemistry_qaqc_endpoint(payload: dict) -> dict:
    return geochemistry_qaqc(payload.get("samples", []))


@router.post("/geochemistry/fluid-inclusions")
async def geochemistry_fluid_inclusions(payload: dict) -> dict:
    return fluid_inclusion_summary(payload.get("measurements", []))


@router.post("/earth-observation/insar-correction")
async def eo_insar_correction(payload: dict) -> dict:
    return earth_observation_correction("insar_tropospheric", payload)


@router.post("/earth-observation/hyperspectral-correction")
async def eo_hyperspectral_correction(payload: dict) -> dict:
    return earth_observation_correction("hyperspectral_atmospheric", payload)


@router.post("/earth-observation/sar-polarimetry")
async def eo_sar_polarimetry(payload: dict) -> dict:
    return earth_observation_correction("sar_polarimetry", payload)


@router.post("/hydro/modpath")
async def hydro_modpath(payload: dict) -> dict:
    return modpath_capture_zone(
        payload.get("wells", []), float(payload.get("porosity", 0.25))
    )


@router.post("/hydro/ert-3d")
async def hydro_ert_3d(payload: dict) -> dict:
    return ert_3d_inversion(
        int(payload.get("profile_count", 4)), int(payload.get("electrode_count", 64))
    )


@router.post("/hydro/groundwater-age")
async def hydro_groundwater_age(payload: dict) -> dict:
    return groundwater_age(payload.get("samples", []))


@router.post("/environment/flood-inundation")
async def environment_flood(payload: dict) -> dict:
    return flood_inundation_model(
        payload.get("dem_url", "minio://dem/matuu.tif"),
        float(payload.get("rainfall_mm", 100)),
        int(payload.get("return_period_years", 100)),
    )


@router.post("/environment/air-quality")
async def environment_air_quality(payload: dict) -> dict:
    return dispersion_model(
        "air",
        float(payload.get("emission_rate", 100)),
        float(payload.get("distance_m", 1000)),
    )


@router.post("/environment/noise")
async def environment_noise(payload: dict) -> dict:
    return dispersion_model(
        "noise",
        float(payload.get("emission_rate", 120)),
        float(payload.get("distance_m", 1000)),
    )


@router.post("/environment/traffic-haulage")
async def environment_traffic(payload: dict) -> dict:
    return traffic_haulage_simulation(
        float(payload.get("production_tpd", 500)),
        float(payload.get("truck_payload_t", 25)),
        float(payload.get("route_km", 120)),
    )


@router.post("/environment/structural-assessment")
async def environment_structural(payload: dict) -> dict:
    return structural_assessment(
        float(payload.get("insar_mm", 0)), float(payload.get("optical_change_score", 0))
    )


@router.post("/platform/lims/sample-event")
async def platform_lims_sample_event(payload: dict) -> dict:
    return lims_sample_event(
        payload.get("sample_id", "S-001"),
        payload.get("status", "collected"),
        payload.get("actor", "field_geologist"),
    )


@router.post("/platform/tenements/obligations")
async def platform_tenement_obligations(payload: dict) -> dict:
    return tenement_obligations(payload.get("licences", []))


@router.post("/platform/data-room")
async def platform_data_room(payload: dict) -> dict:
    return investor_data_room(
        payload.get("project_id", "matuu"),
        payload.get("allowed_layers", ["kriging", "resource_summary"]),
        int(payload.get("ttl_hours", 168)),
    )
