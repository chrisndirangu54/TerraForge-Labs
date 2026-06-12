import io
import json
import uuid

from fastapi.testclient import TestClient

from backend.api.ingest.store import get_ingest_store, reset_ingest_store
from backend.api.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_ingest_store()


def test_capture_catalog_lists_transports_and_formats():
    response = client.get("/capture/catalog")
    assert response.status_code == 200
    body = response.json()
    transport_ids = {item["id"] for item in body["transports"]}
    assert {"file", "bluetooth", "wifi", "radio"}.issubset(transport_ids)
    assert "csv" in body["formats"]
    assert "xrf_bruker" in body["instruments"]


def test_capture_upload_csv_auto_detect():
    project_id = str(uuid.uuid4())
    csv_content = "sample_id,lon,lat,Cu_ppm,Ta_ppm\nS-1,37.5,-1.15,120,88\n"
    response = client.post(
        "/capture/upload",
        data={
            "project_id": project_id,
            "transport": "usb",
            "instrument_type": "auto",
        },
        files={"file": ("survey.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 1
    assert body["display"]["display_type"] in {"table", "map", "mixed", "chart"}
    assert body["display"]["table"]["rows"][0]["Ta_ppm"] == "88" or body["display"]["table"]["rows"][0]["Ta_ppm"] == 88

    stored = get_ingest_store().list_observations(project_id=project_id)
    assert len(stored) == 1


def test_capture_upload_geojson():
    project_id = str(uuid.uuid4())
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [37.51, -1.14]},
                "properties": {"sample_id": "G-1", "ta_ppm": 95},
            }
        ],
    }
    response = client.post(
        "/capture/upload",
        data={"project_id": project_id, "transport": "file"},
        files={
            "file": (
                "points.geojson",
                io.BytesIO(json.dumps(geojson).encode()),
                "application/geo+json",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["file_format"] == "geojson"
    assert body["display"]["map"] is not None


def test_capture_device_scan_connect_sync():
    project_id = str(uuid.uuid4())
    scan = client.get("/capture/devices/scan", params={"transport": "bluetooth"})
    assert scan.status_code == 200
    device = scan.json()["devices"][0]

    connect = client.post(
        f"/capture/devices/{device['device_id']}/connect",
        json={"transport": "bluetooth"},
    )
    assert connect.status_code == 200
    session_id = connect.json()["session_id"]

    sync = client.post(
        f"/capture/devices/sessions/{session_id}/sync",
        json={"project_id": project_id, "count": 3},
    )
    assert sync.status_code == 200
    body = sync.json()
    assert body["row_count"] == 3
    assert body["display"]["table"]["rows"]
    assert len(get_ingest_store().list_observations(project_id=project_id)) == 3


def test_capture_stream_endpoint():
    project_id = str(uuid.uuid4())
    response = client.post(
        "/capture/stream",
        json={
            "project_id": project_id,
            "transport": "wifi",
            "instrument_type": "xrf_bruker",
            "readings": [
                {"sample_id": "W-1", "lon": 37.5, "lat": -1.15, "ta_ppm": 110}
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["row_count"] == 1