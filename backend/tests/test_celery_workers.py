import uuid

import pytest
from fastapi.testclient import TestClient

from backend.api.celery_app import QUEUE_DEFAULT, QUEUE_GPU, QUEUE_REPORTS, TASK_ROUTES
from backend.api.jobs.store import get_job_store, reset_job_store
from backend.api.main import app
from backend.api.tasks import celery_run_kriging

client = TestClient(app)


def test_celery_task_routes_configured():
    assert TASK_ROUTES["terraforge.run_kriging"]["queue"] == QUEUE_DEFAULT
    assert TASK_ROUTES["terraforge.run_deposit_model"]["queue"] == QUEUE_DEFAULT
    assert TASK_ROUTES["terraforge.run_gpu_classification"]["queue"] == QUEUE_GPU
    assert TASK_ROUTES["terraforge.generate_jorc_report"]["queue"] == QUEUE_REPORTS


def test_kriging_async_returns_job_id():
    response = client.post("/fuse-geodata", json={"element": "ta_ppm"})
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] in {"queued", "complete"}
    assert body.get("poll_url", "").startswith("/jobs/")


def test_jorc_async_returns_job_id():
    response = client.post(
        "/reports/jorc",
        json={"project_name": "Async Test", "commodity": "Au"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] in {"queued", "complete"}


def test_kriging_sync_mode():
    response = client.post(
        "/fuse-geodata",
        json={"element": "ta_ppm", "async": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert "result" in body


def test_gpu_capabilities_lists_worker_queues():
    response = client.get("/classification/gpu/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["queue"] == QUEUE_GPU
    assert "default" in body["queues"]
    assert "gpu" in body["queues"]
    assert "reports" in body["queues"]


@pytest.mark.usefixtures("celery_eager_mode")
def test_dead_letter_metadata_after_retries_exhausted(monkeypatch):
    reset_job_store()

    def _boom(_payload: dict) -> dict:
        raise RuntimeError("kriging failed")

    monkeypatch.setattr("backend.api.kriging.run_kriging_pipeline", _boom)

    job_id = str(uuid.uuid4())
    with pytest.raises(RuntimeError):
        celery_run_kriging.apply(args=[job_id, {"element": "ta_ppm"}])

    stored = get_job_store().get(job_id)
    assert stored["status"] == "failed"
    assert stored["dead_letter"]["final"] is True
    assert stored["dead_letter"]["retries"] == 1


@pytest.fixture
def celery_eager_mode():
    from backend.api.celery_app import celery_app

    if celery_app is None:
        pytest.skip("Celery is not available")
    previous = {
        "task_always_eager": celery_app.conf.task_always_eager,
        "task_eager_propagates": celery_app.conf.task_eager_propagates,
    }
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = previous["task_always_eager"]
    celery_app.conf.task_eager_propagates = previous["task_eager_propagates"]
