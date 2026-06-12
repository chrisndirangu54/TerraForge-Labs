from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.api.services.capture_display import build_display_view, build_raster_display
from backend.api.services.device_transports import (
    connect_device,
    disconnect_device,
    list_transports,
    read_device_batch,
    scan_devices,
)
from backend.api.services.ingest import ingest_observations, parser_version_for, rows_to_observations
from shared.instruments.format_router import (
    INSTRUMENT_PARSERS,
    SUPPORTED_FORMATS,
    TRANSPORT_CHANNELS,
    detect_format,
    parse_capture_file,
)

UPLOAD_ROOT = Path("tmp_uploads")
UPLOAD_ROOT.mkdir(exist_ok=True)
_SESSIONS: dict[str, dict[str, Any]] = {}


def capture_catalog() -> dict[str, Any]:
    return {
        "transports": list_transports(),
        "formats": SUPPORTED_FORMATS,
        "instruments": sorted(INSTRUMENT_PARSERS.keys()),
        "transport_channels": TRANSPORT_CHANNELS,
    }


def _record_session(**fields: Any) -> None:
    upload_id = fields["upload_id"]
    _SESSIONS[upload_id] = {
        "upload_id": upload_id,
        "project_id": fields["project_id"],
        "instrument_type": fields["instrument_type"],
        "file_format": fields["file_format"],
        "transport": fields["transport"],
        "filename": fields.get("filename"),
        "row_count": fields["row_count"],
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "display_type": fields["display"].get("display_type"),
    }


def process_file_upload(
    *,
    instrument_type: str | None,
    transport: str,
    filename: str,
    raw_bytes: bytes,
    project_id: str,
    gps_bytes: bytes | None = None,
    calibration_bytes: bytes | None = None,
    gps_filename: str | None = None,
    calibration_filename: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    upload_id = str(uuid.uuid4())
    normalized_instrument = None if instrument_type in {None, "", "auto"} else instrument_type
    upload_dir = UPLOAD_ROOT / "capture" / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    raw_path = upload_dir / (filename or "upload.bin")
    raw_path.write_bytes(raw_bytes)

    gps_path = None
    if gps_bytes:
        gps_path = upload_dir / (gps_filename or "gps.csv")
        gps_path.write_bytes(gps_bytes)

    cal_path = None
    if calibration_bytes:
        cal_path = upload_dir / (calibration_filename or "calibration.json")
        cal_path.write_bytes(calibration_bytes)

    rows, resolved, file_format, meta = parse_capture_file(
        raw_path,
        instrument_type=normalized_instrument,
        filename=filename,
        gps_path=gps_path,
        calibration_path=cal_path,
        project_id=project_id,
    )
    validation = meta["validation"]
    preview = meta["geojson_preview"]
    raster_result = meta.get("raster")

    observations = rows_to_observations(
        rows,
        project_id=project_id,
        source=source or f"capture_{transport}",
        parser_version=parser_version_for(resolved),
        instrument_type=resolved,
        upload_id=upload_id,
    )
    persisted = ingest_observations(observations)

    if raster_result:
        display = build_raster_display(raster_result, instrument_type=resolved, transport=transport, filename=filename)
    else:
        display = build_display_view(
            rows=rows,
            geojson=preview,
            file_format=file_format,
            instrument_type=resolved,
            transport=transport,
            filename=filename,
        )

    _record_session(
        upload_id=upload_id,
        project_id=project_id,
        instrument_type=resolved,
        file_format=file_format,
        transport=transport,
        row_count=len(rows),
        display=display,
        filename=filename,
    )
    (upload_dir / "parsed_preview.json").write_text(json.dumps(preview))

    return {
        "upload_id": upload_id,
        "project_id": project_id,
        "transport": transport,
        "instrument_type": resolved,
        "file_format": file_format,
        "detected_format": detect_format(filename),
        "row_count": len(rows),
        "flagged_count": validation.get("flagged_count", 0),
        "warnings": validation.get("warnings", []),
        "persisted": persisted,
        "display": display,
        "geojson_preview": {**preview, "features": preview.get("features", [])[:25]},
        "storage_url": f"minio://uploads/capture/{upload_id}/{filename}",
    }


def process_stream_capture(
    *,
    transport: str,
    instrument_type: str,
    readings: list[dict[str, Any]],
    project_id: str,
    device_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    upload_id = str(uuid.uuid4())
    rows = list(readings)
    preview = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.get("lon", 37.5), r.get("lat", -1.15)]},
                "properties": r,
            }
            for r in rows
        ],
    }
    observations = rows_to_observations(
        rows,
        project_id=project_id,
        source=f"capture_{transport}",
        parser_version=parser_version_for(instrument_type),
        instrument_type=instrument_type,
        upload_id=upload_id,
    )
    persisted = ingest_observations(observations)
    display = build_display_view(
        rows=rows,
        geojson=preview,
        file_format="stream",
        instrument_type=instrument_type,
        transport=transport,
    )
    _record_session(
        upload_id=upload_id,
        project_id=project_id,
        instrument_type=instrument_type,
        file_format="stream",
        transport=transport,
        row_count=len(rows),
        display=display,
    )
    return {
        "upload_id": upload_id,
        "project_id": project_id,
        "transport": transport,
        "instrument_type": instrument_type,
        "device_id": device_id,
        "session_id": session_id,
        "row_count": len(rows),
        "persisted": persisted,
        "display": display,
    }


def list_capture_sessions(*, project_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    items = list(_SESSIONS.values())
    if project_id:
        items = [item for item in items if item["project_id"] == project_id]
    items.sort(key=lambda row: row["captured_at"], reverse=True)
    return {"items": items[:limit], "count": len(items[:limit])}


def get_capture_display(upload_id: str) -> dict[str, Any] | None:
    session = _SESSIONS.get(upload_id)
    if session is None:
        return None
    preview_path = UPLOAD_ROOT / "capture" / upload_id / "parsed_preview.json"
    geojson = json.loads(preview_path.read_text(encoding="utf-8")) if preview_path.exists() else None
    return {"session": session, "geojson_preview": geojson}


def device_scan(transport: str) -> dict[str, Any]:
    return scan_devices(transport)


def device_connect(device_id: str, transport: str) -> dict[str, Any]:
    return connect_device(device_id, transport)


def device_disconnect(session_id: str) -> dict[str, Any]:
    return disconnect_device(session_id)


def device_sync(*, session_id: str, project_id: str, count: int = 5) -> dict[str, Any]:
    batch = read_device_batch(session_id, count=count)
    result = process_stream_capture(
        transport=batch["transport"],
        instrument_type=batch["instrument_type"],
        readings=batch["readings"],
        project_id=project_id,
        session_id=session_id,
    )
    result["device_batch"] = batch
    return result