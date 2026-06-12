from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

_DEVICE_CATALOG: list[dict[str, Any]] = [
    {
        "device_id": "xrf-bruker-01",
        "name": "Bruker S1 Titan",
        "instrument_type": "xrf_bruker",
        "transports": ["bluetooth", "wifi", "usb"],
        "battery_pct": 78,
        "firmware": "1.8.4",
    },
    {
        "device_id": "kt10-02",
        "name": "Terraplus KT-10",
        "instrument_type": "kappameter",
        "transports": ["bluetooth", "serial"],
        "battery_pct": 64,
        "firmware": "2.1.0",
    },
    {
        "device_id": "trimble-r12",
        "name": "Trimble R12 GNSS",
        "instrument_type": "gnss_trimble",
        "transports": ["bluetooth", "wifi", "radio"],
        "battery_pct": 91,
        "firmware": "6.22",
    },
    {
        "device_id": "terrameter-ls",
        "name": "ABEM Terrameter LS",
        "instrument_type": "terrameter",
        "transports": ["serial", "usb", "wifi"],
        "battery_pct": 100,
        "firmware": "4.0.2",
    },
    {
        "device_id": "iot-gateway-01",
        "name": "Edge IoT Gateway",
        "instrument_type": "xrf_bruker",
        "transports": ["wifi", "radio"],
        "battery_pct": 100,
        "firmware": "0.9.3",
    },
]

_CONNECTIONS: dict[str, dict[str, Any]] = {}


def list_transports() -> list[dict[str, Any]]:
    from shared.instruments.format_router import TRANSPORT_CHANNELS

    return TRANSPORT_CHANNELS


def scan_devices(transport: str) -> dict[str, Any]:
    devices = [
        device
        for device in _DEVICE_CATALOG
        if transport in device["transports"] or transport == "file"
    ]
    return {
        "transport": transport,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "devices": devices,
    }


def connect_device(device_id: str, transport: str) -> dict[str, Any]:
    device = next((d for d in _DEVICE_CATALOG if d["device_id"] == device_id), None)
    if device is None:
        raise KeyError(f"Unknown device: {device_id}")
    if transport not in device["transports"]:
        raise ValueError(f"Device {device_id} does not support transport {transport}")

    session_id = str(uuid.uuid4())
    _CONNECTIONS[session_id] = {
        "session_id": session_id,
        "device_id": device_id,
        "transport": transport,
        "instrument_type": device["instrument_type"],
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "status": "connected",
    }
    return {**_CONNECTIONS[session_id], "device": device}


def disconnect_device(session_id: str) -> dict[str, Any]:
    session = _CONNECTIONS.pop(session_id, None)
    if session is None:
        raise KeyError(f"Unknown session: {session_id}")
    session["status"] = "disconnected"
    return session


def read_device_batch(session_id: str, *, count: int = 5) -> dict[str, Any]:
    session = _CONNECTIONS.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session: {session_id}")

    instrument = session["instrument_type"]
    rows: list[dict[str, Any]] = []
    base_lon, base_lat = 37.48 + random.uniform(-0.02, 0.02), -1.15 + random.uniform(-0.02, 0.02)

    for index in range(max(1, min(count, 25))):
        if instrument == "xrf_bruker":
            ta = round(random.uniform(40, 180), 1)
            rows.append(
                {
                    "sample_id": f"XRF-{index + 1:03d}",
                    "lon": base_lon + index * 0.0004,
                    "lat": base_lat + index * 0.0002,
                    "ta_ppm": ta,
                    "nb_ppm": round(ta * 0.4, 1),
                    "acquisition_time_s": 42,
                    "flagged": ta < 50,
                }
            )
        elif instrument == "kappameter":
            si = round(random.uniform(0.001, 0.08), 4)
            rows.append(
                {
                    "sample_id": f"KT10-{index + 1:03d}",
                    "lon": base_lon,
                    "lat": base_lat,
                    "susceptibility_si": si,
                    "temperature_c": 28,
                    "flagged": si > 0.05,
                }
            )
        elif instrument == "gnss_trimble":
            rows.append(
                {
                    "point_id": f"GNSS-{index + 1:03d}",
                    "lon": base_lon + index * 0.0001,
                    "lat": base_lat,
                    "elevation_m": 1180 + index,
                    "fix_quality": 4,
                    "hdop": 0.9,
                    "flagged": False,
                }
            )
        else:
            rows.append(
                {
                    "profile_id": f"P-{index + 1:02d}",
                    "lon": base_lon,
                    "lat": base_lat,
                    "apparent_resistivity_ohm_m": round(random.uniform(80, 400), 1),
                    "ip_chargeability_ms": round(random.uniform(1, 6), 2),
                    "flagged": False,
                }
            )

    return {
        "session_id": session_id,
        "transport": session["transport"],
        "instrument_type": instrument,
        "readings": rows,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }