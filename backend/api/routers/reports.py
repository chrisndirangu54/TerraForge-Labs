from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.tasks import celery_generate_jorc_report, generate_jorc_report

router = APIRouter()


@router.post("/reports/jorc")
async def generate_jorc(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    return submit_job(
        job_type="jorc_report",
        payload=payload,
        runner=generate_jorc_report,
        celery_task=celery_generate_jorc_report,
        async_default=True,
        user=user,
    )
