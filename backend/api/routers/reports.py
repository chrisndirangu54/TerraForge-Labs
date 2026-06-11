from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.services.jorc_report import (
    acknowledge_disclaimer,
    get_report_store,
    transition_report_state,
)
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


@router.get("/reports/jorc/{report_id}")
async def get_jorc_report(report_id: str) -> dict:
    report = get_report_store().get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/reports/jorc/{report_id}/transition")
async def transition_jorc_report(
    report_id: str,
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    target_state = payload.get("state")
    if not target_state:
        raise HTTPException(status_code=400, detail="state is required")
    try:
        report = transition_report_state(
            report_id,
            target_state=target_state,
            actor=user.get("email", user.get("id", "system")),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return report


@router.post("/reports/jorc/{report_id}/acknowledge-disclaimer")
async def acknowledge_jorc_disclaimer(
    report_id: str,
    user: dict = Depends(require_mutating_access),
) -> dict:
    try:
        return acknowledge_disclaimer(report_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
