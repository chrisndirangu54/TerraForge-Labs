from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.auth.projects import require_project_id_when_authenticated
from backend.api.services import capture as capture_service

router = APIRouter(prefix="/capture", tags=["capture"])


@router.get("/catalog")
async def capture_catalog(_: dict = Depends(get_current_user)) -> dict:
    return capture_service.capture_catalog()


@router.get("/sessions")
async def capture_sessions(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _: dict = Depends(get_current_user),
) -> dict:
    return capture_service.list_capture_sessions(project_id=project_id, limit=limit)


@router.get("/sessions/{upload_id}")
async def capture_session_detail(
    upload_id: str,
    _: dict = Depends(get_current_user),
) -> dict:
    detail = capture_service.get_capture_display(upload_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Capture session not found")
    return detail


@router.post("/upload")
async def capture_upload(
    file: UploadFile = File(...),
    instrument_type: str | None = Form(default=None),
    transport: str = Form(default="file"),
    project_id: str | None = Form(default=None),
    gps_file: UploadFile | None = File(default=None),
    calibration_file: UploadFile | None = File(default=None),
    user: dict = Depends(require_mutating_access),
) -> dict:
    resolved_project = require_project_id_when_authenticated(user, project_id)
    if not resolved_project:
        import uuid

        resolved_project = str(uuid.uuid4())

    return capture_service.process_file_upload(
        instrument_type=instrument_type,
        transport=transport,
        filename=file.filename or "upload.bin",
        raw_bytes=await file.read(),
        project_id=resolved_project,
        gps_bytes=await gps_file.read() if gps_file else None,
        calibration_bytes=await calibration_file.read() if calibration_file else None,
        gps_filename=gps_file.filename if gps_file else None,
        calibration_filename=calibration_file.filename if calibration_file else None,
    )


@router.post("/stream")
async def capture_stream(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    readings = payload.get("readings")
    if not isinstance(readings, list) or not readings:
        raise HTTPException(status_code=400, detail="readings[] required")

    project_id = require_project_id_when_authenticated(user, payload.get("project_id"))
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id required")

    instrument_type = str(payload.get("instrument_type", "generic_csv"))
    transport = str(payload.get("transport", "wifi"))
    return capture_service.process_stream_capture(
        transport=transport,
        instrument_type=instrument_type,
        readings=readings,
        project_id=str(project_id),
        device_id=payload.get("device_id"),
        session_id=payload.get("session_id"),
    )


@router.get("/devices/scan")
async def capture_device_scan(
    transport: str = Query(default="bluetooth"),
    _: dict = Depends(get_current_user),
) -> dict:
    return capture_service.device_scan(transport)


@router.post("/devices/{device_id}/connect")
async def capture_device_connect(
    device_id: str,
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    transport = str(payload.get("transport", "bluetooth"))
    try:
        return capture_service.device_connect(device_id, transport)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/devices/sessions/{session_id}/disconnect")
async def capture_device_disconnect(
    session_id: str,
    _: dict = Depends(require_mutating_access),
) -> dict:
    try:
        return capture_service.device_disconnect(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/devices/sessions/{session_id}/sync")
async def capture_device_sync(
    session_id: str,
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    project_id = require_project_id_when_authenticated(user, payload.get("project_id"))
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id required")
    try:
        return capture_service.device_sync(
            session_id=session_id,
            project_id=str(project_id),
            count=int(payload.get("count", 5)),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc