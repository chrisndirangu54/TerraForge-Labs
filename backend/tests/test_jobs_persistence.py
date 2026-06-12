import uuid

from backend.api.jobs.memory_store import MemoryJobStore
from backend.api.jobs.store import reset_job_store
from backend.api.tasks import generate_jorc_report, run_gpu_classification


def test_memory_job_store_tracks_status_history():
    store = MemoryJobStore()
    job_id = str(uuid.uuid4())

    store.set(job_id, {"job_type": "jorc_report", "status": "queued"})
    store.set(job_id, {"job_type": "jorc_report", "status": "running"})
    store.set(
        job_id,
        {
            "job_type": "jorc_report",
            "status": "complete",
            "result": {"report": "ok"},
        },
    )

    current = store.get(job_id)
    assert current["status"] == "complete"
    assert current["result"]["report"] == "ok"

    events = store.get_events(job_id)
    statuses = [event["status"] for event in events]
    assert statuses == ["queued", "running", "complete"]


def test_jorc_report_updates_job_store():
    reset_job_store()
    job_id = str(uuid.uuid4())
    generate_jorc_report(job_id, {"project_name": "Test", "commodity": "Au"})

    from backend.api.jobs.store import get_job_store

    stored = get_job_store().get(job_id)
    assert stored["status"] == "complete"
    assert stored["job_type"] == "jorc_report"
    assert "result" in stored


def test_gpu_classification_job_lifecycle():
    reset_job_store()
    job_id = str(uuid.uuid4())
    run_gpu_classification(job_id, {"task": "mineral", "project_id": "demo"})

    from backend.api.jobs.store import get_job_store

    stored = get_job_store().get(job_id)
    assert stored["status"] == "complete"
    assert stored["job_type"] == "gpu_classification"
    assert stored["result"]["task"] == "mineral"