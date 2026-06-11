from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_gpu_capabilities_endpoint():
    response = client.get("/classification/gpu/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert "mineral" in body["supported_tasks"]
    assert "device" in body


def test_gpu_sync_classification_mineral():
    response = client.post(
        "/classification/gpu/sync",
        json={"task": "mineral", "project_id": "test-project"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    result = body["result"]
    assert result["task"] == "mineral"
    assert "label" in result
    assert "confidence" in result
    assert "top3" in result


def test_gpu_batch_classification():
    response = client.post(
        "/classification/gpu/batch",
        json={
            "task": "geobotany",
            "items": [
                {"project_id": "a", "lon": 37.5, "lat": -1.15},
                {"project_id": "b", "lon": 37.6, "lat": -1.16},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert body["result"]["count"] == 2


def test_gpu_async_job_poll():
    response = client.post(
        "/classification/gpu",
        json={"task": "thin_section", "async": False},
    )
    assert response.status_code == 200
    body = response.json()
    job_id = body["job_id"]
    poll = client.get(f"/jobs/{job_id}")
    assert poll.status_code == 200
    polled = poll.json()
    assert polled["status"] == "complete"
    assert polled["result"]["task"] == "thin_section"
