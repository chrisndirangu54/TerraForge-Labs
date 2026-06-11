import io
import uuid

from fastapi.testclient import TestClient

from backend.api.ingest.store import get_ingest_store, reset_ingest_store
from backend.api.main import app
from backend.api.services.ingest import rows_to_observations

client = TestClient(app)


def setup_function() -> None:
    reset_ingest_store()


def test_rows_to_observations_maps_metadata():
    rows = [
        {
            "sample_id": "XRF-001",
            "lon": 37.5,
            "lat": -1.15,
            "ta_ppm": 120.0,
            "flagged": True,
            "flag_reasons": ["high_error"],
        }
    ]
    observations = rows_to_observations(
        rows,
        project_id=str(uuid.uuid4()),
        source="test",
        parser_version="xrf_bruker@1.0.0",
        instrument_type="xrf_bruker",
    )
    assert len(observations) == 1
    obs = observations[0]
    assert obs.sample_id == "XRF-001"
    assert obs.lon == 37.5
    assert obs.crs == "EPSG:4326"
    assert obs.data["ta_ppm"] == 120.0
    assert obs.flagged is True


def test_ingest_observations_endpoint():
    project_id = str(uuid.uuid4())
    response = client.post(
        "/ingest/observations",
        json={
            "observations": [
                {
                    "project_id": project_id,
                    "source": "api_ingest",
                    "parser_version": "manual@1.0.0",
                    "crs": "EPSG:4326",
                    "instrument_type": "field_note",
                    "sample_id": "FN-1",
                    "lon": 37.51,
                    "lat": -1.14,
                    "data": {"note": "outcrop sampled"},
                }
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 1
    assert body["project_id"] == project_id
    assert body["crs"] == "EPSG:4326"

    listed = client.get("/ingest/observations", params={"project_id": project_id})
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["sample_id"] == "FN-1"
    assert items[0]["source"] == "api_ingest"


def test_ingest_requires_observations_list():
    response = client.post("/ingest/observations", json={})
    assert response.status_code == 400


def test_instrument_upload_persists_rows():
    csv_content = (
        "Spectrum Label,Ta_Concentration,Nb_Concentration,Sn_Concentration,"
        "Ta_Error,Acquisition_Time,lon,lat,timestamp,Method\n"
        "XRF-001,100,200,10,5,45,37.5,-1.15,2026-01-01,GeoExploration\n"
    )
    project_id = str(uuid.uuid4())
    response = client.post(
        "/instruments/upload",
        data={"instrument_type": "xrf_bruker", "project_id": project_id},
        files={"file": ("sample.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 1
    assert body["project_id"] == project_id
    assert body["persisted"]["inserted"] == 1

    stored = get_ingest_store().list_observations(project_id=project_id)
    assert len(stored) == 1
    assert stored[0]["parser_version"] == "xrf_bruker@1.0.0"
    assert stored[0]["source"] == "instrument_upload"
