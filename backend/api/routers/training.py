from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.tasks import (
    celery_pull_datasets,
    celery_train_geobotany,
    celery_train_mineral,
    pull_datasets,
    train_geobotany,
    train_mineral,
)

router = APIRouter()


@router.post("/training/datasets/pull", dependencies=[Depends(require_mutating_access)])
async def pull_training_datasets(payload: dict | None = None) -> dict:
    body = payload or {}
    return submit_job(
        job_type="dataset_pull",
        payload=body,
        runner=pull_datasets,
        celery_task=celery_pull_datasets,
        async_default=bool(body.get("async", False)),
        meta={"pipeline": "dataset_pull"},
        user={"id": body.get("user_id", "system")},
    )


@router.post("/training/{task}/run", dependencies=[Depends(require_mutating_access)])
async def run_training(task: str, payload: dict | None = None) -> dict:
    body = payload or {}
    normalized = task.lower()
    if normalized == "mineral":
        return submit_job(
            job_type="mineral_train",
            payload=body,
            runner=train_mineral,
            celery_task=celery_train_mineral,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "mineral_train"},
            user={"id": body.get("user_id", "system")},
        )
    if normalized == "geobotany":
        return submit_job(
            job_type="geobotany_train",
            payload=body,
            runner=train_geobotany,
            celery_task=celery_train_geobotany,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "geobotany_train"},
            user={"id": body.get("user_id", "system")},
        )
    raise HTTPException(status_code=404, detail=f"Unknown training task: {task}")