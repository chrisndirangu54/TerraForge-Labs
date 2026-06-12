from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.tasks import celery_run_deposit_model, run_deposit_model

router = APIRouter()


@router.post("/deposit-model")
async def generate_deposit_model(
    payload: dict,
    _: dict = Depends(require_mutating_access),
) -> dict:
    return submit_job(
        job_type="deposit_model",
        payload=payload,
        runner=run_deposit_model,
        celery_task=celery_run_deposit_model,
        async_default=True,
    )