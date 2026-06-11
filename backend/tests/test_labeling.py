from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.labeling_store import reset_labeling_store

client = TestClient(app)


def setup_function() -> None:
    reset_labeling_store()


def test_label_queue_crud_and_confirm():
    created = client.post(
        "/labeling/queue",
        json={
            "species": "unknown_vegetation",
            "confidence": 0.41,
            "lon": 37.5,
            "lat": -1.15,
            "project_id": "matuu",
        },
    )
    assert created.status_code == 200
    item_id = created.json()["id"]

    listed = client.get("/labeling/queue")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    confirmed = client.post(
        f"/labeling/queue/{item_id}/confirm",
        json={"confirmed_label": "ocimum_centraliafricanum"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["confirmed_label"] == "ocimum_centraliafricanum"

    deleted = client.delete(f"/labeling/queue/{item_id}")
    assert deleted.status_code == 200
    assert client.get("/labeling/queue").json()["count"] == 0
