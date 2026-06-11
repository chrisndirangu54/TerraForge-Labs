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


def _mark_dead_letter(
    job_id: str,
    job_type: str,
    exc: Exception,
    *,
    retries: int,
    task_name: str,
) -> None:
    _set(
        job_id,
        job_type,
        status="failed",
        error=str(exc),
        dead_letter={
            "reason": str(exc),
            "job_type": job_type,
            "task": task_name,
            "retries": retries,
            "final": True,
        },
    )


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


def _wrap_celery_task(name: str, job_type: str, runner):
    if celery_app is None:
        return None

    max_retries = 1

    @celery_app.task(bind=True, name=name)
    def _task(self, job_id: str, payload: dict) -> dict:
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return runner(job_id, payload)
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    continue
                _mark_dead_letter(
                    job_id,
                    job_type,
                    exc,
                    retries=attempt,
                    task_name=name,
                )
                raise
        assert last_exc is not None
        raise last_exc

    return _task


celery_run_kriging = _wrap_celery_task("terraforge.run_kriging", "kriging", run_kriging)
celery_run_deposit_model = _wrap_celery_task(
    "terraforge.run_deposit_model", "deposit_model", run_deposit_model
)
celery_generate_jorc_report = _wrap_celery_task(
    "terraforge.generate_jorc_report", "jorc_report", generate_jorc_report
)
celery_gpu_classification = _wrap_celery_task(
    "terraforge.run_gpu_classification", "gpu_classification", run_gpu_classification
)
