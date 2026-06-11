from __future__ import annotations

from backend.api.celery_app import celery_app
from backend.api.jobs.store import JobStore, get_job_store
from backend.processing.deposit_model import generate_deposit_model_files
from backend.processing.gpu_classifier import classify_gpu, classify_gpu_batch


def _store() -> JobStore:
    return get_job_store()


def _set(job_id: str, job_type: str, **data: object) -> None:
    store = _store()
    store.set(job_id, {"job_type": job_type, **data})


def run_kriging(job_id: str, payload: dict) -> dict:
    from backend.api.kriging import run_kriging_pipeline

    _set(job_id, "kriging", status="running")
    result = run_kriging_pipeline(payload)
    _set(job_id, "kriging", status="complete", result=result)
    return result


def run_deposit_model(job_id: str, payload: dict) -> dict:
    _set(job_id, "deposit_model", status="running")
    result = generate_deposit_model_files(payload)
    _set(job_id, "deposit_model", status="complete", result=result)
    return result


def generate_jorc_report(job_id: str, payload: dict) -> dict:
    from backend.api.services.jorc_report import build_jorc_report

    _set(job_id, "jorc_report", status="running")
    result = build_jorc_report(payload)
    _set(job_id, "jorc_report", status="complete", result=result)
    return result


def run_gpu_classification(job_id: str, payload: dict) -> dict:
    task = payload.get("task", "mineral")
    _set(job_id, "gpu_classification", status="running", task=task, accelerator="gpu")

    if payload.get("batch"):
        result = classify_gpu_batch(task, payload.get("items", []))
    else:
        result = classify_gpu(task, payload)

    _set(
        job_id,
        "gpu_classification",
        status="complete",
        task=task,
        accelerator=result.get("accelerator", "gpu"),
        result=result,
    )
    return result


if celery_app is not None:

    @celery_app.task(name="terraforge.run_gpu_classification")
    def celery_gpu_classification(job_id: str, payload: dict) -> dict:
        return run_gpu_classification(job_id, payload)
