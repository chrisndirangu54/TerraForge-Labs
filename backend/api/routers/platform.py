from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.services.artifact_lineage import (
    anchor_hash_on_chain,
    list_lineage,
    record_lineage,
)
from backend.processing.gap_closure import investor_data_room
from backend.processing.platform_expansion import (
    aeromag_radiometrics_fusion,
    assay_qaqc_pipeline,
    biogeochem_correlation,
    conformal_grade_intervals,
    core_tray_segment,
    climate_risk_npv,
    drone_cv_analyze,
    evidence_bundle,
    exploration_stop_criterion,
    federated_consent_register,
    field_agent_sync,
    fusion_score_v2,
    geomagnetism_analyze,
    gpr_interpret,
    iot_stream_ingest,
    lidar_process,
    live_npv_digital_twin,
    marketplace_checkout,
    modflow_coupling,
    nema_compliance_check,
    plate_tectonics_context,
    drill_plan_v2,
    seismological_summary,
    submit_3d_inversion_job,
    uav_survey_ingest,
)

router = APIRouter(prefix="/platform", tags=["platform"])


@router.post("/fusion/v2")
async def platform_fusion_v2(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return fusion_score_v2(payload)


@router.post("/drill/plan-v2")
async def platform_drill_plan_v2(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return drill_plan_v2(payload)


@router.post("/geochem/qaqc-pipeline")
async def platform_qaqc_pipeline(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return assay_qaqc_pipeline(payload)


@router.post("/lineage/record")
async def platform_lineage_record(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return record_lineage(
        artifact_type=str(payload.get("artifact_type", "generic")),
        storage_key=str(payload.get("storage_key", "unknown")),
        job_id=payload.get("job_id"),
        project_id=payload.get("project_id"),
        model_version=payload.get("model_version"),
        dataset_hash=payload.get("dataset_hash"),
        parent_hashes=payload.get("parent_hashes"),
        metadata=payload.get("metadata"),
    )


@router.get("/lineage/list")
async def platform_lineage_list(
    project_id: str | None = None,
    limit: int = 50,
    _: dict = Depends(get_current_user),
) -> dict:
    return {"records": list_lineage(project_id=project_id, limit=limit)}


@router.post("/blockchain/anchor")
async def platform_blockchain_anchor(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    record_id = payload.get("record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="record_id required")
    try:
        return anchor_hash_on_chain(str(record_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/data-room/v2")
async def platform_data_room_v2(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    room = investor_data_room(
        str(payload.get("project_id", "demo")),
        payload.get("sections", ["geology", "financials", "models"]),
    )
    bundle = evidence_bundle(payload)
    return {**room, "evidence_bundle": bundle}


@router.post("/uav/survey")
async def platform_uav_survey(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return uav_survey_ingest(payload)


@router.post("/aeromag/fusion")
async def platform_aeromag(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return aeromag_radiometrics_fusion(payload)


@router.post("/biogeochem/correlate")
async def platform_biogeochem(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return biogeochem_correlation(payload)


@router.post("/field-agent/sync")
async def platform_field_agent(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return field_agent_sync(payload)


@router.post("/digital-twin/live-npv")
async def platform_live_npv(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return live_npv_digital_twin(payload)


@router.post("/inversion/submit")
async def platform_inversion_submit(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return submit_3d_inversion_job(payload)


@router.post("/hydro/modflow-coupling")
async def platform_modflow(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return modflow_coupling(payload)


@router.post("/compliance/nema")
async def platform_nema(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return nema_compliance_check(payload)


@router.post("/conformal/grade")
async def platform_conformal(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return conformal_grade_intervals(payload)


@router.post("/geomagnetism/analyze")
async def platform_geomag(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return geomagnetism_analyze(payload)


@router.post("/tectonics/context")
async def platform_tectonics(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return plate_tectonics_context(payload)


@router.post("/seismic/summary")
async def platform_seismic(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return seismological_summary(payload)


@router.post("/lidar/process")
async def platform_lidar(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return lidar_process(payload)


@router.post("/drone/cv/analyze")
async def platform_drone_cv(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return drone_cv_analyze(payload)


@router.post("/gpr/interpret")
async def platform_gpr(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return gpr_interpret(payload)


@router.post("/iot/ingest")
async def platform_iot(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return iot_stream_ingest(payload)


@router.post("/exploration/stop-criterion")
async def platform_stop_criterion(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return exploration_stop_criterion(payload)


@router.post("/evidence-bundle")
async def platform_evidence_bundle(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return evidence_bundle(payload)


@router.post("/federated/consent")
async def platform_federated_consent(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return federated_consent_register(payload)


@router.post("/core-tray/segment")
async def platform_core_tray(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return core_tray_segment(payload)


@router.post("/climate-risk/npv")
async def platform_climate_npv(payload: dict, _: dict = Depends(get_current_user)) -> dict:
    return climate_risk_npv(payload)


@router.post("/marketplace/checkout")
async def platform_marketplace_checkout(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return marketplace_checkout(payload)