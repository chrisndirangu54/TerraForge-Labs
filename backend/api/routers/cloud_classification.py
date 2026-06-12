from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.celery_app import celery_app
from backend.api.jobs.store import get_job_store
from backend.api.tasks import run_gpu_classification
from backend.processing.gpu_classifier import (
    SUPPORTED_TASKS,
    classify_gpu_batch,
    get_device_info,
)

router = APIRouter()


def _enqueue_or_run(payload: dict) -> dict:
    store = get_job_store()
    task = payload.get("task", "mineral")
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=400, detail=f"Unsupported task: {task}")

    job_id = str(uuid.uuid4())
    use_async = bool(payload.get("async", True))

    if use_async and celery_app is not None:
        from backend.api.tasks import celery_gpu_classification

        store.set(
            job_id,
            {
                "job_type": "gpu_classification",
                "status": "queued",
                "task": task,
                "accelerator": "gpu-queue",
            },
        )
        celery_gpu_classification.delay(job_id, payload)
        return {
            "job_id": job_id,
            "status": "queued",
            "task": task,
            "poll_url": f"/jobs/{job_id}",
        }

    run_gpu_classification(job_id, payload)
    stored = store.get(job_id)
    return {"job_id": job_id, **stored}


@router.get("/classification/gpu/capabilities")
async def gpu_capabilities() -> dict:
    from backend.api.celery_app import QUEUE_DEFAULT, QUEUE_GPU, QUEUE_REPORTS

    device = get_device_info()
    return {
        "supported_tasks": list(SUPPORTED_TASKS),
        "device": device,
        "queue": QUEUE_GPU,
        "queues": [QUEUE_DEFAULT, QUEUE_GPU, QUEUE_REPORTS],
        "async_default": True,
    }


@router.post("/classification/gpu")
async def submit_gpu_classification(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    return _enqueue_or_run(payload)


@router.post("/classification/gpu/sync")
async def submit_gpu_classification_sync(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    payload = {**payload, "async": False}
    return _enqueue_or_run(payload)


@router.post("/classification/gpu/batch")
async def submit_gpu_classification_batch(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    store = get_job_store()
    task = payload.get("task", "mineral")
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=400, detail=f"Unsupported task: {task}")

    items = payload.get("items", [])
    if not items:
        items = [
            {
                "project_id": payload.get("project_id", "batch-demo"),
                "lon": payload.get("lon", 37.5),
                "lat": payload.get("lat", -1.15),
            }
        ]

    if payload.get("async", False) and celery_app is not None:
        job_id = str(uuid.uuid4())
        batch_payload = {"task": task, "items": items, "batch": True}
        from backend.api.tasks import celery_gpu_classification

        store.set(
            job_id,
            {
                "job_type": "gpu_classification",
                "status": "queued",
                "task": task,
                "batch": True,
                "count": len(items),
            },
        )
        celery_gpu_classification.delay(job_id, batch_payload)
        return {
            "job_id": job_id,
            "status": "queued",
            "task": task,
            "count": len(items),
            "poll_url": f"/jobs/{job_id}",
        }

    result = classify_gpu_batch(task, items)
    return {"status": "complete", "result": result}