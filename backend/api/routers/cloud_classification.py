from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.celery_app import QUEUE_GPU, celery_app
from backend.api.jobs.enqueue import submit_job
from backend.api.tasks import celery_gpu_classification, run_gpu_classification
from backend.processing.gpu_classifier import (
    SUPPORTED_TASKS,
    classify_gpu_batch,
    get_device_info,
)

router = APIRouter()


@router.get("/classification/gpu/capabilities")
async def gpu_capabilities() -> dict:
    device = get_device_info()
    return {
        "supported_tasks": list(SUPPORTED_TASKS),
        "device": device,
        "queue": QUEUE_GPU if celery_app is not None else "in-process",
        "queues": {
            "default": ["kriging", "deposit_model"],
            "gpu": ["classification"],
            "reports": ["jorc_report"],
        },
        "async_default": True,
    }


@router.post("/classification/gpu")
async def submit_gpu_classification(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    task = payload.get("task", "mineral")
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=400, detail=f"Unsupported task: {task}")
    return submit_job(
        job_type="gpu_classification",
        payload=payload,
        runner=run_gpu_classification,
        celery_task=celery_gpu_classification,
        meta={"task": task, "accelerator": "gpu-queue"},
        async_default=True,
    )


@router.post("/classification/gpu/sync")
async def submit_gpu_classification_sync(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    task = payload.get("task", "mineral")
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=400, detail=f"Unsupported task: {task}")
    payload = {**payload, "async": False}
    return submit_job(
        job_type="gpu_classification",
        payload=payload,
        runner=run_gpu_classification,
        celery_task=celery_gpu_classification,
        meta={"task": task},
        async_default=False,
    )


@router.post("/classification/gpu/batch")
async def submit_gpu_classification_batch(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
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

    batch_payload = {**payload, "task": task, "items": items, "batch": True}
    if payload.get("async", False):
        return submit_job(
            job_type="gpu_classification",
            payload=batch_payload,
            runner=run_gpu_classification,
            celery_task=celery_gpu_classification,
            meta={"task": task, "batch": True, "count": len(items)},
            async_default=True,
        )

    result = classify_gpu_batch(task, items)
    return {"status": "complete", "result": result}
