from __future__ import annotations

from backend.api.celery_app import celery_app
from backend.processing.deposit_model import generate_deposit_model_files
from backend.processing.gpu_classifier import classify_gpu, classify_gpu_batch

JOB_STORE: dict[str, dict] = {}


def run_kriging(job_id: str, payload: dict) -> dict:
    from backend.api.kriging import run_kriging_pipeline

    JOB_STORE[job_id] = {"status": "running"}
    result = run_kriging_pipeline(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result


def run_deposit_model(job_id: str, payload: dict) -> dict:
    JOB_STORE[job_id] = {"status": "running"}
    result = generate_deposit_model_files(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result


def generate_jorc_report(job_id: str, payload: dict) -> dict:
    from backend.api.services.jorc_report import build_jorc_report

    JOB_STORE[job_id] = {"status": "running"}
    result = build_jorc_report(payload)
    JOB_STORE[job_id] = {"status": "complete", "result": result}
    return result


def run_gpu_classification(job_id: str, payload: dict) -> dict:
    task = payload.get("task", "mineral")
    JOB_STORE[job_id] = {"status": "running", "task": task, "accelerator": "gpu"}

    if payload.get("batch"):
        result = classify_gpu_batch(task, payload.get("items", []))
    else:
        result = classify_gpu(task, payload)

    JOB_STORE[job_id] = {
        "status": "complete",
        "task": task,
        "accelerator": result.get("accelerator", "gpu"),
        "result": result,
    }
    return result


if celery_app is not None:

    @celery_app.task(name="terraforge.run_gpu_classification")
    def celery_gpu_classification(job_id: str, payload: dict) -> dict:
        return run_gpu_classification(job_id, payload)
