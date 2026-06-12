from __future__ import annotations

from backend.api.celery_app import celery_app
from backend.api.jobs.store import get_job_store


def _set(job_id: str, job_type: str, **data: object) -> None:
    store = get_job_store()
    record = {"job_type": job_type, **data}
    store.set(job_id, record)
    if record.get("status") == "complete":
        try:
            from backend.api.services.rag_indexer import index_completed_job

            index_completed_job(job_id, {"job_id": job_id, **record})
        except Exception:
            pass


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


def run_lidar_process(job_id: str, payload: dict) -> dict:
    from backend.processing.lidar_pipeline import process_lidar_to_cogs

    _set(job_id, "lidar_process", status="running")
    result = process_lidar_to_cogs(payload)
    _set(job_id, "lidar_process", status="complete", result=result)
    return result


def run_uav_survey(job_id: str, payload: dict) -> dict:
    from backend.processing.uav_pipeline import process_uav_survey

    _set(job_id, "uav_survey", status="running")
    result = process_uav_survey(payload)
    _set(job_id, "uav_survey", status="complete", result=result)
    return result


def run_3d_inversion(job_id: str, payload: dict) -> dict:
    from backend.processing.inversion_pipeline import process_3d_inversion

    _set(job_id, "inversion_3d", status="running")
    result = process_3d_inversion(payload)
    _set(job_id, "inversion_3d", status="complete", result=result)
    return result


celery_run_lidar_process = _wrap_celery_task(
    "terraforge.run_lidar_process", "lidar_process", run_lidar_process
)
celery_run_uav_survey = _wrap_celery_task(
    "terraforge.run_uav_survey", "uav_survey", run_uav_survey
)
celery_run_3d_inversion = _wrap_celery_task(
    "terraforge.run_3d_inversion", "inversion_3d", run_3d_inversion
)