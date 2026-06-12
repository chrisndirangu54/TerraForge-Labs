from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.instruments.biogeochemical_parser import BiogeochemicalParser
from shared.instruments.generic_csv import GenericCsvParser
from shared.instruments.generic_geojson import GenericGeoJsonParser
from shared.instruments.gnss_trimble import GnssTrimbleParser
from shared.instruments.kappameter import KappameterParser
from shared.instruments.lidar_capture import parse_lidar_file
from shared.instruments.pdf_report import PdfReportParser
from shared.instruments.terrameter import TerrameterParser
from shared.instruments.xrf_bruker import XrfBrukerParser

INSTRUMENT_PARSERS: dict[str, type[Any]] = {
    "xrf_bruker": XrfBrukerParser,
    "xrf_olympus": GenericCsvParser,
    "terrameter": TerrameterParser,
    "kappameter": KappameterParser,
    "gnss_trimble": GnssTrimbleParser,
    "magnetometer": GenericCsvParser,
    "gravimeter": GenericCsvParser,
    "radiometer": GenericCsvParser,
    "em_conductivity": GenericCsvParser,
    "ip_resistivity": GenericCsvParser,
    "tdem": GenericCsvParser,
    "seismograph": GenericCsvParser,
    "water_quality": GenericCsvParser,
    "petrographic": GenericCsvParser,
    "survey_station": GenericCsvParser,
    "drone_generic": GenericCsvParser,
    "drone_dji": GenericCsvParser,
    "biogeochemical": BiogeochemicalParser,
    "soil_gas": GenericCsvParser,
    "hydrogeology": GenericCsvParser,
    "downhole_geophysics": GenericCsvParser,
    "lidar": GenericCsvParser,
    "generic_csv": GenericCsvParser,
    "generic_geojson": GenericGeoJsonParser,
    "pdf_report": PdfReportParser,
}

SUPPORTED_FORMATS = {
    "csv": {"extensions": [".csv"], "mime": ["text/csv", "application/csv"]},
    "tsv": {"extensions": [".tsv"], "mime": ["text/tab-separated-values"]},
    "xml": {"extensions": [".xml"], "mime": ["application/xml", "text/xml"]},
    "json": {"extensions": [".json"], "mime": ["application/json"]},
    "geojson": {
        "extensions": [".geojson"],
        "mime": ["application/geo+json"],
    },
    "pdf": {"extensions": [".pdf"], "mime": ["application/pdf"]},
    "nmea": {"extensions": [".nmea", ".txt"], "mime": ["text/plain"]},
    "lidar": {
        "extensions": [".las", ".laz"],
        "mime": ["application/octet-stream", "application/las"],
    },
}

TRANSPORT_CHANNELS = [
    {
        "id": "file",
        "label": "File upload",
        "description": "Drag-drop or browse CSV, PDF, XML, GeoJSON, LAZ",
        "implemented": True,
        "protocol": "multipart",
    },
    {
        "id": "usb",
        "label": "USB / mass storage",
        "description": "Instrument export from USB stick or field laptop",
        "implemented": True,
        "protocol": "file_import",
    },
    {
        "id": "bluetooth",
        "label": "Bluetooth LE",
        "description": "Browser Web Bluetooth or gateway sync",
        "implemented": True,
        "protocol": "ble_gatt",
    },
    {
        "id": "wifi",
        "label": "Wi-Fi / TCP",
        "description": "Drone controllers, IoT gateways, edge XRF",
        "implemented": True,
        "protocol": "tcp_stream",
    },
    {
        "id": "radio",
        "label": "Radio / mesh",
        "description": "LoRa field mesh and VHF relay for offline camps",
        "implemented": True,
        "protocol": "lora_mesh",
    },
    {
        "id": "serial",
        "label": "Serial / RS-232",
        "description": "Legacy terrameter and survey total stations",
        "implemented": True,
        "protocol": "serial_csv_export",
    },
]


def detect_format(filename: str, content_type: str | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".las", ".laz"}:
        return "lidar"
    if suffix == ".geojson":
        return "geojson"
    for fmt, meta in SUPPORTED_FORMATS.items():
        if suffix in meta["extensions"]:
            return fmt
    if content_type:
        lowered = content_type.lower()
        for fmt, meta in SUPPORTED_FORMATS.items():
            if lowered in meta["mime"]:
                return fmt
    return "binary"


def resolve_instrument(
    instrument_type: str | None,
    file_format: str,
) -> str:
    if instrument_type and instrument_type in INSTRUMENT_PARSERS:
        return instrument_type
    if file_format == "lidar":
        return "lidar"
    if file_format == "pdf":
        return "pdf_report"
    if file_format in {"csv", "tsv"}:
        return "generic_csv"
    if file_format == "geojson":
        return "generic_geojson"
    if file_format == "xml":
        return "terrameter"
    if file_format == "nmea":
        return "gnss_trimble"
    return instrument_type or "generic_csv"


def parse_capture_file(
    filepath: Path,
    *,
    instrument_type: str | None = None,
    filename: str | None = None,
    gps_path: Path | None = None,
    calibration_path: Path | None = None,
    project_id: str | None = None,
) -> tuple[list[dict], str, str, dict]:
    name = filename or filepath.name
    file_format = detect_format(name)
    resolved = resolve_instrument(instrument_type, file_format)

    if file_format == "lidar":
        rows, meta = parse_lidar_file(
            filepath, project_id=project_id or "capture"
        )
        return rows, "lidar", file_format, meta

    parser_cls = INSTRUMENT_PARSERS.get(resolved, GenericCsvParser)
    parser = parser_cls()

    if resolved == "xrf_bruker":
        rows = parser.parse(filepath, str(gps_path) if gps_path else None)
        validation = parser.validate(rows)
        rows = parser.calibrate(rows, str(calibration_path) if calibration_path else None)
        preview = parser.to_geojson(rows)
    elif resolved == "terrameter":
        rows = parser.parse(filepath)
        validation = {
            "warnings": [],
            "flagged_count": sum(int(r.get("flagged", False)) for r in rows),
        }
        preview = parser.to_geojson(rows)
    elif resolved == "biogeochemical":
        rows = parser.parse(filepath)
        validation = {
            "warnings": [],
            "flagged_count": sum(int(r.get("flagged", False)) for r in rows),
        }
        preview = parser.to_geojson(rows)
    elif hasattr(parser, "to_geojson"):
        rows = parser.parse(filepath)
        validation = {
            "warnings": [],
            "flagged_count": sum(int(r.get("flagged", False)) for r in rows),
        }
        preview = parser.to_geojson(rows)
    else:
        rows = parser.parse(filepath)
        validation = {
            "warnings": [],
            "flagged_count": sum(int(r.get("flagged", False)) for r in rows),
        }
        preview = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [r.get("lon", 0), r.get("lat", 0)],
                    },
                    "properties": r,
                }
                for r in rows[:50]
            ],
        }

    return rows, resolved, file_format, {
        "validation": validation,
        "geojson_preview": preview,
    }