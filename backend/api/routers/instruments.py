from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from shared.instruments.gnss_trimble import GnssTrimbleParser
from shared.instruments.kappameter import KappameterParser
from shared.instruments.terrameter import TerrameterParser
from shared.instruments.xrf_bruker import XrfBrukerParser

router = APIRouter()

UPLOAD_ROOT = Path("tmp_uploads")
UPLOAD_ROOT.mkdir(exist_ok=True)

PARSER_REGISTRY = {
    "xrf_bruker": XrfBrukerParser,
    "terrameter": TerrameterParser,
    "kappameter": KappameterParser,
    "gnss_trimble": GnssTrimbleParser,
}


@router.post("/instruments/upload")
async def upload_instrument_file(
    instrument_type: str = Form(...),
    file: UploadFile = File(...),
    gps_file: UploadFile | None = File(default=None),
    calibration_file: UploadFile | None = File(default=None),
) -> dict:
    if instrument_type not in PARSER_REGISTRY:
        return {"error": f"Unsupported instrument_type: {instrument_type}"}

    upload_id = str(uuid.uuid4())
    upload_dir = UPLOAD_ROOT / instrument_type / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    raw_path = upload_dir / file.filename
    raw_path.write_bytes(await file.read())

    gps_path = None
    if gps_file:
        gps_path = upload_dir / gps_file.filename
        gps_path.write_bytes(await gps_file.read())

    cal_path = None
    if calibration_file:
        cal_path = upload_dir / calibration_file.filename
        cal_path.write_bytes(await calibration_file.read())

    parser = PARSER_REGISTRY[instrument_type]()
    if instrument_type == "xrf_bruker":
        rows = parser.parse(raw_path, str(gps_path) if gps_path else None)
        validation = parser.validate(rows)
        rows = parser.calibrate(rows, str(cal_path) if cal_path else None)
        preview = parser.to_geojson(rows)
    else:
        rows = parser.parse(raw_path)
        validation = {"warnings": [], "flagged_count": sum(int(r.get("flagged", False)) for r in rows)}
        preview = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.get("lon", 0), r.get("lat", 0)]}, "properties": r}
                for r in rows[:10]
            ],
        }

    storage_path = upload_dir / "parsed_preview.json"
    storage_path.write_text(json.dumps(preview))

    return {
        "upload_id": upload_id,
        "row_count": len(rows),
        "flagged_count": validation.get("flagged_count", 0),
        "warnings": validation.get("warnings", []),
        "geojson_preview": {**preview, "features": preview.get("features", [])[:10]},
        "minio_url": f"minio://uploads/{instrument_type}/{upload_id}/{file.filename}",
    }
