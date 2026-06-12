from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.services.exploration_summary import build_deposit_summary_response
from backend.api.services.response_display import enrich_response
from backend.api.tasks import celery_run_deposit_model, run_deposit_model

router = APIRouter()


@router.get("/deposit/summary")
async def deposit_summary(
    project_id: str | None = Query(default=None),
    _: dict = Depends(get_current_user),
) -> dict:
    return enrich_response(build_deposit_summary_response(project_id=project_id))


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