from __future__ import annotations

import math
from statistics import mean, pstdev

PATHFINDER_ELEMENTS = {
    "epithermal_au": ["As", "Sb", "Hg", "Se", "Te"],
    "orogenic_au": ["As", "Sb", "Bi", "Te", "W"],
    "porphyry_cu": ["Mo", "Re", "Se", "Te", "Bi"],
    "sediment_hosted_cu": ["Co", "Ag", "As", "Se", "U"],
    "critical_metals": ["Li", "Rb", "Cs", "Ta", "Nb", "Sn"],
}

QAQC_STD_FAIL_THRESHOLD_PCT = 10.0
QAQC_DUPLICATE_RPD_THRESHOLD_PCT = 20.0
QAQC_BLANK_CONTAMINATION_FACTOR = 5.0
DRILL_COST_PER_M_USD = 180.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def pathfinder_analysis(
    samples: list[dict], deposit_style: str = "orogenic_au"
) -> dict:
    elements = PATHFINDER_ELEMENTS.get(
        deposit_style, PATHFINDER_ELEMENTS["orogenic_au"]
    )
    scores: dict[str, float] = {}
    for element in elements:
        values = [float(sample.get(element, 0.0)) for sample in samples]
        if not values:
            scores[element] = 0.0
            continue
        background = mean(values)
        spread = pstdev(values) or 1.0
        scores[element] = max((max(values) - background) / spread, 0.0)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    high_samples = [
        sample
        for sample in samples
        if any(
            float(sample.get(el, 0.0)) > mean([float(s.get(el, 0.0)) for s in samples])
            for el in elements
        )
    ]
    if high_samples:
        source_lon = mean([float(sample.get("lon", 0.0)) for sample in high_samples])
        source_lat = mean([float(sample.get("lat", 0.0)) for sample in high_samples])
    else:
        source_lon = source_lat = 0.0
    return {
        "deposit_style": deposit_style,
        "ranked_pathfinders": [
            {"element": element, "halo_score": round(score, 3)}
            for element, score in ranked
        ],
        "dispersion_vector": {
            "toward_lon": round(source_lon, 6),
            "toward_lat": round(source_lat, 6),
        },
        "recommended_follow_up": "step-out soil lines and first-pass drill fence toward ranked halo centroid",
    }


def soil_gas_interpretation(readings: list[dict]) -> dict:
    co2_values = [float(row.get("co2_ppm", 0.0)) for row in readings]
    rn_values = [float(row.get("radon_bq_m3", 0.0)) for row in readings]
    he_values = [float(row.get("helium_ppm", 0.0)) for row in readings]
    co2_threshold = (mean(co2_values) if co2_values else 0.0) + 2 * (
        pstdev(co2_values) if len(co2_values) > 1 else 0.0
    )
    radon_threshold = (mean(rn_values) if rn_values else 0.0) + 2 * (
        pstdev(rn_values) if len(rn_values) > 1 else 0.0
    )
    helium_threshold = (mean(he_values) if he_values else 0.0) + 2 * (
        pstdev(he_values) if len(he_values) > 1 else 0.0
    )
    anomalies = [
        row
        for row in readings
        if float(row.get("co2_ppm", 0.0)) >= co2_threshold
        or float(row.get("radon_bq_m3", 0.0)) >= radon_threshold
        or float(row.get("helium_ppm", 0.0)) >= helium_threshold
    ]
    return {
        "sample_count": len(readings),
        "anomaly_count": len(anomalies),
        "fault_or_geothermal_signal": len(anomalies) > 0,
        "anomaly_geojson_url": "minio://geochemistry/soil_gas_anomalies.geojson",
    }


def sequential_gaussian_simulation(
    samples: list[dict], realisations: int = 100
) -> dict:
    values = [
        float(sample.get("grade", sample.get("ta_ppm", 0.0))) for sample in samples
    ]
    avg = mean(values) if values else 0.0
    spread = pstdev(values) if len(values) > 1 else max(avg * 0.1, 1.0)
    p10 = max(0.0, avg - 1.2816 * spread)
    p90 = avg + 1.2816 * spread
    return {
        "method": "sequential_gaussian_simulation_stub",
        "realisations": realisations,
        "mean_grade": round(avg, 3),
        "p10_grade": round(p10, 3),
        "p90_grade": round(p90, 3),
        "risk_cube_url": "minio://geostat/sgs_risk_cube.zarr",
        "jorc_support": "resource classification uncertainty envelope",
    }


def optimise_drill_plan(
    targets: list[dict], budget_usd: float, max_depth_m: float = 250.0
) -> dict:
    ranked = sorted(
        targets,
        key=lambda item: _safe_ratio(
            float(item.get("uncertainty_reduction", 0.0))
            * float(item.get("target_probability", 0.0)),
            float(item.get("depth_m", max_depth_m)),
        ),
        reverse=True,
    )
    selected = []
    spend = 0.0
    for target in ranked:
        depth = min(float(target.get("depth_m", max_depth_m)), max_depth_m)
        cost = depth * DRILL_COST_PER_M_USD
        if spend + cost <= budget_usd:
            selected.append(
                {
                    **target,
                    "estimated_cost_usd": round(cost, 2),
                    "information_gain": round(
                        float(target.get("uncertainty_reduction", 0.0))
                        * float(target.get("target_probability", 0.0)),
                        3,
                    ),
                }
            )
            spend += cost
    return {
        "selected_holes": selected,
        "planned_metres": round(
            sum(float(hole.get("depth_m", max_depth_m)) for hole in selected), 2
        ),
        "estimated_spend_usd": round(spend, 2),
        "remaining_budget_usd": round(budget_usd - spend, 2),
    }


def geochemistry_qaqc(samples: list[dict]) -> dict:
    failures = []
    for sample in samples:
        sample_type = sample.get("sample_type", "unknown")
        if sample_type == "standard":
            expected = float(sample.get("expected_ppm", 0.0))
            measured = float(sample.get("measured_ppm", 0.0))
            pct_error = abs(_safe_ratio(measured - expected, expected)) * 100
            if pct_error > QAQC_STD_FAIL_THRESHOLD_PCT:
                failures.append(
                    {
                        "sample_id": sample.get("sample_id"),
                        "failure": "standard_drift",
                        "pct_error": round(pct_error, 2),
                    }
                )
        if (
            sample_type == "blank"
            and float(sample.get("measured_ppm", 0.0))
            > float(sample.get("detection_limit_ppm", 0.0))
            * QAQC_BLANK_CONTAMINATION_FACTOR
        ):
            failures.append(
                {"sample_id": sample.get("sample_id"), "failure": "blank_contamination"}
            )
        if sample_type == "duplicate":
            original = float(sample.get("original_ppm", 0.0))
            duplicate = float(sample.get("duplicate_ppm", 0.0))
            rpd = (
                abs(original - duplicate) / max((original + duplicate) / 2, 0.001) * 100
            )
            if rpd > QAQC_DUPLICATE_RPD_THRESHOLD_PCT:
                failures.append(
                    {
                        "sample_id": sample.get("sample_id"),
                        "failure": "duplicate_precision",
                        "rpd": round(rpd, 2),
                    }
                )
    return {
        "sample_count": len(samples),
        "failure_count": len(failures),
        "failures": failures,
        "jorc_ready": len(failures) == 0,
    }


def lims_sample_event(sample_id: str, status: str, actor: str) -> dict:
    allowed = [
        "collected",
        "prepared",
        "dispatched",
        "received_by_lab",
        "assayed",
        "validated",
    ]
    if status not in allowed:
        raise ValueError(f"unsupported LIMS status: {status}")
    return {
        "sample_id": sample_id,
        "status": status,
        "actor": actor,
        "chain_of_custody_url": f"minio://lims/{sample_id}/chain_of_custody.json",
        "next_status": allowed[min(allowed.index(status) + 1, len(allowed) - 1)],
    }


def tenement_obligations(licences: list[dict]) -> dict:
    obligations = []
    for licence in licences:
        obligations.append(
            {
                "licence_id": licence.get("licence_id"),
                "expiry_date": licence.get("expiry_date"),
                "annual_report_due": licence.get("annual_report_due"),
                "expenditure_commitment_usd": float(
                    licence.get("expenditure_commitment_usd", 0.0)
                ),
                "alert_level": (
                    "high" if licence.get("days_to_expiry", 999) <= 90 else "normal"
                ),
            }
        )
    return {"licence_count": len(licences), "obligations": obligations}


def investor_data_room(
    project_id: str, allowed_layers: list[str], ttl_hours: int = 168
) -> dict:
    return {
        "project_id": project_id,
        "allowed_layers": allowed_layers,
        "ttl_hours": ttl_hours,
        "access_url": f"https://data-room.terraforge.local/{project_id}/redacted",
        "audit_event_url": f"minio://audit/{project_id}/data_room_access.json",
        "raw_data_hidden": True,
    }


def fluid_inclusion_summary(measurements: list[dict]) -> dict:
    homogenisation = [float(row.get("homogenisation_c", 0.0)) for row in measurements]
    salinity = [float(row.get("salinity_wt_pct_nacl", 0.0)) for row in measurements]
    avg_temp = mean(homogenisation) if homogenisation else 0.0
    avg_salinity = mean(salinity) if salinity else 0.0
    inferred_system = (
        "magmatic_hydrothermal"
        if avg_temp >= 300 and avg_salinity >= 10
        else "epithermal_or_meteoric_mixed"
    )
    return {
        "measurement_count": len(measurements),
        "average_homogenisation_c": round(avg_temp, 2),
        "average_salinity_wt_pct_nacl": round(avg_salinity, 2),
        "inferred_fluid_system": inferred_system,
    }


def earth_observation_correction(kind: str, payload: dict) -> dict:
    outputs = {
        "insar_tropospheric": "minio://eo/gacos_corrected_insar.tif",
        "hyperspectral_atmospheric": "minio://eo/6s_atcor_reflectance_cube.bsq",
        "sar_polarimetry": "minio://eo/sentinel1_vv_vh_decomposition.tif",
    }
    return {
        "correction": kind,
        "input": payload.get("input_url", "minio://eo/input.tif"),
        "output_url": outputs.get(kind, "minio://eo/corrected_output.tif"),
        "method": {
            "insar_tropospheric": "GACOS + GNSS zenith wet delay correction",
            "hyperspectral_atmospheric": "6S/ATCOR reflectance retrieval scaffold",
            "sar_polarimetry": "VV/VH surface-volume-double-bounce proxy decomposition",
        }.get(kind, "generic_correction"),
    }


def modpath_capture_zone(wells: list[dict], porosity: float = 0.25) -> dict:
    return {
        "well_count": len(wells),
        "porosity": porosity,
        "capture_zone_url": "minio://hydrogeology/modpath_capture_zones.geojson",
        "particle_tracks_url": "minio://hydrogeology/modpath_particle_tracks.geojson",
    }


def ert_3d_inversion(profile_count: int, electrode_count: int) -> dict:
    cells = max(1, profile_count * electrode_count * 4)
    return {
        "profile_count": profile_count,
        "electrode_count": electrode_count,
        "inversion_cells": cells,
        "aquifer_volume_url": "minio://hydrogeology/ert_3d_aquifer_volume.vtk",
        "rms_misfit": 1.08,
    }


def groundwater_age(samples: list[dict]) -> dict:
    ages = []
    for sample in samples:
        tritium = float(sample.get("tritium_tu", 0.0))
        cfc = float(sample.get("cfc12_pptv", 0.0))
        age = max(0.0, 55 - tritium * 8 - cfc * 0.02)
        ages.append(age)
    return {
        "sample_count": len(samples),
        "mean_residence_time_years": round(mean(ages), 2) if ages else 0.0,
        "sustainable_yield_note": "older groundwater requires conservative abstraction limits",
    }


def flood_inundation_model(
    dem_url: str, rainfall_mm: float, return_period_years: int = 100
) -> dict:
    inundated_area = max(0.1, rainfall_mm * return_period_years / 10_000)
    return {
        "engine": "HEC-RAS_or_LISFLOOD_FP_stub",
        "dem_url": dem_url,
        "return_period_years": return_period_years,
        "inundated_area_km2": round(inundated_area, 3),
        "depth_grid_url": "minio://environment/flood_depth_grid.tif",
    }


def dispersion_model(kind: str, emission_rate: float, distance_m: float) -> dict:
    concentration = emission_rate / max(distance_m, 1.0) ** 1.2
    return {
        "model": "AERMOD_stub" if kind == "air" else "blast_noise_attenuation_stub",
        "kind": kind,
        "predicted_at_receptor": round(concentration, 4),
        "compliance_map_url": f"minio://environment/{kind}_dispersion.geojson",
    }


def traffic_haulage_simulation(
    production_tpd: float, truck_payload_t: float, route_km: float
) -> dict:
    trips_per_day = math.ceil(production_tpd / max(truck_payload_t, 1.0))
    return {
        "trips_per_day": trips_per_day,
        "route_km": route_km,
        "daily_truck_km": round(trips_per_day * route_km * 2, 2),
        "road_wear_index": round(trips_per_day * route_km / 100, 3),
    }


def structural_assessment(insar_mm: float, optical_change_score: float) -> dict:
    risk = min(100.0, abs(insar_mm) * 3 + optical_change_score * 40)
    return {
        "risk_score": round(risk, 2),
        "structurally_compromised": risk >= 60,
        "inspection_priority": (
            "urgent" if risk >= 80 else "field_check" if risk >= 60 else "monitor"
        ),
    }
