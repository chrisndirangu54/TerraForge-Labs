from __future__ import annotations

import hashlib
import math
from statistics import mean, pstdev
from typing import Any

from backend.api.services.artifact_lineage import content_hash, record_lineage
from backend.processing.gap_closure import geochemistry_qaqc, optimise_drill_plan


def fusion_score_v2(payload: dict[str, Any]) -> dict[str, Any]:
    """Multi-source fusion with kriging uncertainty, geobotany, mag/structure attribution."""

    weights = {
        "kriging_grade": 0.28,
        "kriging_uncertainty": 0.12,
        "geobotany": 0.18,
        "geochemistry": 0.15,
        "aeromag_structure": 0.12,
        "lidar_slope_access": 0.08,
        "tectonic_proximity": 0.07,
        **(payload.get("weights") or {}),
    }
    sources = payload.get("sources", payload)
    contributions: dict[str, float] = {}
    attributions: list[dict[str, Any]] = []

    for source, weight in weights.items():
        raw = sources.get(source, sources.get(f"{source}_score", 0.0))
        if isinstance(raw, dict):
            value = float(raw.get("score", raw.get("value", 0.0)))
        else:
            value = float(raw)
        if source == "kriging_uncertainty":
            # Lower uncertainty → higher contribution
            normalised = max(0.0, 1.0 - min(value, 1.0))
        else:
            normalised = max(0.0, min(1.0, value / 100.0 if value > 1 else value))
        contrib = round(normalised * weight, 4)
        contributions[source] = contrib
        attributions.append(
            {
                "source": source,
                "weight": weight,
                "raw_value": value,
                "contribution": contrib,
                "shap_style_rank": 0,
            }
        )

    attributions.sort(key=lambda row: row["contribution"], reverse=True)
    for index, row in enumerate(attributions):
        row["shap_style_rank"] = index + 1

    fusion_score = round(sum(contributions.values()), 4)
    classification = (
        "high_priority"
        if fusion_score >= 0.72
        else "moderate" if fusion_score >= 0.48 else "low_priority"
    )

    return {
        "fusion_score": fusion_score,
        "classification": classification,
        "contributions": contributions,
        "attributions": attributions,
        "weights": weights,
        "recommended_action": (
            "Scout drill high-attribution cells; refresh kriging after QA/QC pass"
            if classification == "high_priority"
            else "Acquire UAV/LiDAR and infill geochem on top 3 attribution drivers"
        ),
        "evidence_bundle_id": content_hash({"fusion": fusion_score, "sources": sources})[:16],
    }


def drill_plan_v2(payload: dict[str, Any]) -> dict[str, Any]:
    """Budget-aware drill plan with access (LiDAR slope) and information gain."""

    targets = payload.get("targets", [])
    budget_usd = float(payload.get("budget_usd", 500_000))
    max_slope_deg = float(payload.get("max_slope_deg", 25.0))

    scored: list[dict[str, Any]] = []
    for target in targets:
        fusion = float(target.get("fusion_score", target.get("base_score", 50.0)))
        if fusion <= 1.0:
            fusion *= 100.0
        slope = float(target.get("slope_deg", 12.0))
        uncertainty = float(target.get("kriging_variance", 0.5))
        access_penalty = 0.0 if slope <= max_slope_deg else (slope - max_slope_deg) * 2.0
        info_gain = uncertainty * 40.0
        priority = fusion * 0.5 + info_gain * 0.35 - access_penalty * 0.15
        scored.append({**target, "priority_score": round(priority, 2), "access_ok": slope <= max_slope_deg})

    scored.sort(key=lambda row: row["priority_score"], reverse=True)
    base_plan = optimise_drill_plan(scored, budget_usd=budget_usd)
    return {
        **base_plan,
        "planner_version": "v2_information_gain",
        "max_slope_deg": max_slope_deg,
        "ranked_targets": scored[:20],
        "methodology": "fusion + kriging uncertainty reduction + LiDAR access filter",
    }


def uav_survey_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_id", "demo"))
    flight_id = str(payload.get("flight_id", "uav-001"))
    ortho_key = f"uav/{project_id}/{flight_id}/orthomosaic.tif"
    dsm_key = f"uav/{project_id}/{flight_id}/dsm.tif"
    lineage = record_lineage(
        artifact_type="uav_orthomosaic",
        storage_key=ortho_key,
        project_id=project_id,
        metadata={"flight_id": flight_id, "drone": payload.get("drone_model", "dji_generic")},
    )
    return {
        "status": "processed",
        "project_id": project_id,
        "flight_id": flight_id,
        "orthomosaic_cog": ortho_key,
        "dsm_cog": dsm_key,
        "change_detection_vs_sentinel2": f"rasters/{project_id}/uav_change_{flight_id}.tif",
        "geobotany_retrain_trigger": True,
        "lineage_id": lineage["id"],
    }


def aeromag_radiometrics_fusion(payload: dict[str, Any]) -> dict[str, Any]:
    mag = float(payload.get("mag_amplitude_nt", 120.0))
    radio_k = float(payload.get("radiometric_k_percent", 2.5))
    structure_dist_km = float(payload.get("structure_distance_km", 1.2))
    structure_likelihood = max(0.0, min(1.0, (mag / 200.0) * 0.5 + (radio_k / 5.0) * 0.3 + (1.0 / max(structure_dist_km, 0.1)) * 0.2))
    return {
        "structure_likelihood": round(structure_likelihood, 4),
        "mag_amplitude_nt": mag,
        "radiometric_k_percent": radio_k,
        "structure_distance_km": structure_dist_km,
        "layer_url": f"mapping/cog/aeromag/{payload.get('project_id', 'demo')}_structure.tif",
        "recommended_follow_up": "Ground mag walk + structural mapping on high-likelihood corridor",
    }


def biogeochem_correlation(payload: dict[str, Any]) -> dict[str, Any]:
    samples = payload.get("samples", [])
    species = payload.get("species", "haumaniastrum_katangense")
    correlations: dict[str, float] = {}
    for element in ("Cu", "Co", "Ta", "Nb", "Fe"):
        values = [float(s.get(element, s.get(f"{element.lower()}_ppm", 0.0))) for s in samples]
        if values:
            correlations[element] = round(mean(values) / max(pstdev(values) if len(values) > 1 else 1.0, 1e-6), 3)
    top = max(correlations.items(), key=lambda item: item[1], default=("Cu", 0.0))
    return {
        "species": species,
        "sample_count": len(samples),
        "element_correlations": correlations,
        "top_indicator_element": top[0],
        "updated_geobotany_weight": round(min(0.35, 0.15 + top[1] * 0.02), 3),
        "recommended_action": f"Increase {species} sampling density along {top[0]} halo",
    }


def field_agent_sync(payload: dict[str, Any]) -> dict[str, Any]:
    queued = payload.get("queued_observations", [])
    photos = payload.get("photos", [])
    return {
        "synced_observations": len(queued),
        "synced_photos": len(photos),
        "kriging_refresh_job": f"job-kriging-{content_hash(payload)[:8]}",
        "geobotany_retrain_queued": any(photo.get("low_confidence") for photo in photos),
        "offline_mode": payload.get("offline", True),
    }


def live_npv_digital_twin(payload: dict[str, Any]) -> dict[str, Any]:
    from backend.processing.ore_financials import analyze_ore_economics

    base = analyze_ore_economics(payload)
    price_shock = float(payload.get("price_shock_pct", 0.0))
    grade_shock = float(payload.get("grade_shock_pct", 0.0))
    npv_base = float(base["metrics"]["npv_usd"])
    npv_low = npv_base * (1.0 + min(price_shock, grade_shock) / 100.0 * -0.5)
    npv_high = npv_base * (1.0 + max(price_shock, grade_shock) / 100.0 * 0.4)
    return {
        "timestamp_utc": payload.get("as_of"),
        "npv_band_usd": {"p10": round(npv_low, 0), "p50": round(npv_base, 0), "p90": round(npv_high, 0)},
        "commodity": base["commodity"],
        "grade_ta_ppm": base["inputs"].get("grade"),
        "price_feed": payload.get("price_feed", "static"),
        "alerts": ["NPV sensitive to Ta price" if abs(price_shock) > 10 else "stable"],
    }


def submit_3d_inversion_job(payload: dict[str, Any]) -> dict[str, Any]:
    method = payload.get("method", "mt")
    job_id = f"inv3d-{content_hash(payload)[:10]}"
    return {
        "job_id": job_id,
        "method": method,
        "status": "queued",
        "partner_pipeline": "external_inversion_stub",
        "deliverables": ["resistivity_volume.vtk", "uncertainty_cube.nc"],
        "estimated_hours": 48 if method == "mt" else 72,
    }


def modflow_coupling(payload: dict[str, Any]) -> dict[str, Any]:
    pit_depth_m = float(payload.get("pit_depth_m", 80.0))
    dewatering_capex_usd = pit_depth_m * 12_500
    return {
        "modflow_model_id": payload.get("model_id", "modflow-demo"),
        "pit_depth_m": pit_depth_m,
        "dewatering_capex_usd": round(dewatering_capex_usd, 0),
        "npv_impact_usd": round(-dewatering_capex_usd * 0.85, 0),
        "nema_water_report_required": pit_depth_m > 50,
    }


def nema_compliance_check(payload: dict[str, Any]) -> dict[str, Any]:
    activities = payload.get("activities", ["drilling", "exploration_access"])
    risk_flags = []
    if "pit" in activities:
        risk_flags.append("dust_and_water_discharge")
    if "blasting" in activities:
        risk_flags.append("noise_vibration_community")
    return {
        "jurisdiction": "Kenya_NEMA",
        "activities": activities,
        "risk_flags": risk_flags,
        "eia_required": len(risk_flags) > 1,
        "compliance_pack_url": f"compliance/nema/{payload.get('project_id', 'demo')}.pdf",
    }


def conformal_grade_intervals(payload: dict[str, Any]) -> dict[str, Any]:
    grades = [float(v) for v in payload.get("grades", [80, 120, 95, 140, 110])]
    alpha = float(payload.get("alpha", 0.1))
    avg = mean(grades)
    spread = pstdev(grades) if len(grades) > 1 else max(avg * 0.1, 5.0)
    z = 1.645 if alpha <= 0.1 else 1.96
    return {
        "method": "conformal_split_stub",
        "alpha": alpha,
        "mean_grade": round(avg, 2),
        "interval_ppm": {
            "lower": round(max(0.0, avg - z * spread), 2),
            "upper": round(avg + z * spread, 2),
        },
        "coverage_target": 1.0 - alpha,
        "jorc_appendix_ready": True,
    }


def geomagnetism_analyze(payload: dict[str, Any]) -> dict[str, Any]:
    total_field = float(payload.get("total_field_nt", 38000.0))
    gradient = float(payload.get("gradient_nt_m", 2.5))
    anomaly_score = min(1.0, abs(gradient) / 10.0)
    return {
        "total_field_nt": total_field,
        "gradient_nt_m": gradient,
        "anomaly_score": round(anomaly_score, 4),
        "interpretation": "mafic/ultramafic contact candidate" if anomaly_score > 0.4 else "background",
        "layer_url": f"mapping/cog/geomag/{payload.get('project_id', 'demo')}.tif",
    }


def plate_tectonics_context(payload: dict[str, Any]) -> dict[str, Any]:
    lon = float(payload.get("lon", 37.5))
    lat = float(payload.get("lat", -1.15))
    return {
        "craton_margin_distance_km": round(abs(lat + 1.0) * 111.0, 1),
        "nearest_fault_system": "Aswa-Guinea_mobile_belt_stub",
        "deposit_style_prior": ["pegmatite_ta_nb", "sediment_hosted_cu_co"],
        "coordinates": {"lon": lon, "lat": lat},
        "tectonic_layer_url": "mapping/layers#tectonic_faults",
    }


def seismological_summary(payload: dict[str, Any]) -> dict[str, Any]:
    events = payload.get("events", [])
    return {
        "event_count": len(events),
        "max_magnitude": max((float(e.get("magnitude", 0)) for e in events), default=0.0),
        "passive_seismic_recommended": len(events) < 3,
        "deep_target_signal": "low" if len(events) < 5 else "moderate",
    }


def lidar_process(payload: dict[str, Any]) -> dict[str, Any]:
    key = payload.get("storage_key", "lidar/demo.laz")
    lineage = record_lineage(
        artifact_type="lidar_point_cloud",
        storage_key=str(key),
        project_id=str(payload.get("project_id", "demo")),
    )
    return {
        "dtm_cog": str(key).replace(".laz", "_dtm.tif"),
        "slope_cog": str(key).replace(".laz", "_slope.tif"),
        "line_of_sight_drill_access": True,
        "lineage_id": lineage["id"],
    }


def drone_cv_analyze(payload: dict[str, Any]) -> dict[str, Any]:
    frames = int(payload.get("frame_count", 120))
    return {
        "frames_analyzed": frames,
        "alteration_polygons": max(1, frames // 40),
        "haul_road_width_m": 6.5,
        "geobotany_keyframes": max(3, frames // 30),
        "model": "geobotany_domain_cnn",
    }


def gpr_interpret(payload: dict[str, Any]) -> dict[str, Any]:
    depth_m = float(payload.get("max_depth_m", 8.0))
    reflections = int(payload.get("reflection_count", 4))
    return {
        "max_depth_m": depth_m,
        "shallow_structure_detected": reflections >= 2,
        "water_table_candidate_m": round(depth_m * 0.35, 2),
        "use_case_fit": "infrastructure_archaeology_shallow" if depth_m < 15 else "deep_ore_low",
    }


def iot_stream_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    readings = payload.get("readings", [])
    flagged = [r for r in readings if r.get("flagged") or float(r.get("count_rate_cps", 999)) < 100]
    return {
        "ingested": len(readings),
        "flagged_qaqc": len(flagged),
        "instruments": list({r.get("instrument_type", "xrf_bruker") for r in readings}),
        "auto_kriging_hold": len(flagged) > 0,
    }


def exploration_stop_criterion(payload: dict[str, Any]) -> dict[str, Any]:
    marginal_npv = float(payload.get("marginal_npv_next_hole_usd", 250_000))
    hole_cost = float(payload.get("next_hole_cost_usd", 45_000))
    continue_drilling = marginal_npv > hole_cost * 1.5
    return {
        "marginal_npv_next_hole_usd": marginal_npv,
        "next_hole_cost_usd": hole_cost,
        "continue_campaign": continue_drilling,
        "bayesian_stopping_ratio": round(marginal_npv / max(hole_cost, 1), 2),
        "recommendation": "drill" if continue_drilling else "pause_for_infill_geochem",
    }


def evidence_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_id", "demo"))
    bundle_id = content_hash(payload)[:16]
    return {
        "bundle_id": bundle_id,
        "project_id": project_id,
        "sections": {
            "maps": payload.get("map_layers", []),
            "models": payload.get("model_versions", []),
            "financials": payload.get("economics_preview"),
            "citations": payload.get("citations", []),
        },
        "export_url": f"minio://data-room/{project_id}/evidence_{bundle_id}.json",
        "lineage_root_hash": content_hash({"bundle_id": bundle_id, "project_id": project_id}),
    }


def federated_consent_register(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "consent_id": content_hash(payload)[:12],
        "participant_org": payload.get("org", "anonymous_junior"),
        "data_classes": payload.get("data_classes", ["geobotany_labels"]),
        "federated_round": payload.get("round", 1),
        "status": "registered",
    }


def core_tray_segment(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "rqd_pct": float(payload.get("rqd_pct", 72.0)),
        "fracture_count": int(payload.get("fracture_count", 14)),
        "lithology_strips": payload.get("lithology_strips", ["pegmatite", "mica_schist"]),
        "model": "core_tray_cv_stub",
    }


def climate_risk_npv(payload: dict[str, Any]) -> dict[str, Any]:
    from backend.processing.ore_financials import analyze_ore_economics

    base = analyze_ore_economics(payload.get("economics", payload))
    water_stress = float(payload.get("water_stress_index", 0.3))
    flood_risk = float(payload.get("flood_risk_index", 0.2))
    energy_shock = float(payload.get("energy_price_shock_pct", 5.0))
    npv = float(base["metrics"]["npv_usd"])
    adjustment = -npv * (water_stress * 0.08 + flood_risk * 0.06 + energy_shock / 100.0 * 0.04)
    return {
        "base_npv_usd": round(npv, 0),
        "climate_adjusted_npv_usd": round(npv + adjustment, 0),
        "commodity": base["commodity"],
        "water_stress_index": water_stress,
        "flood_risk_index": flood_risk,
        "energy_price_shock_pct": energy_shock,
        "method": "climate_risk_npv_stub",
    }


def assay_qaqc_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    samples = payload.get("samples", payload.get("assays", []))
    qaqc = geochemistry_qaqc(samples)
    return {
        **qaqc,
        "pipeline": "assay_qaqc_v1",
        "hold_kriging": bool(qaqc.get("failures")),
        "recommended_action": "reassay_failed_standards" if qaqc.get("failures") else "release_to_resource_model",
    }


def marketplace_checkout(payload: dict[str, Any]) -> dict[str, Any]:
    plugin_id = str(payload.get("plugin_id", "aseg_gdf2"))
    provider = str(payload.get("provider", "stripe"))
    checkout_id = content_hash(payload)[:12]
    return {
        "checkout_id": checkout_id,
        "provider": provider,
        "plugin_id": plugin_id,
        "status": "sandbox_ok",
        "receipt_id": f"rcpt-{checkout_id}",
        "installed_endpoints": [f"/parse-{plugin_id.replace('_', '-')}"],
    }