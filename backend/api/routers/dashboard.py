from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import get_current_user
from backend.api.jobs.store import get_job_store
from backend.api.services.exploration_summary import build_exploration_summary
from backend.api.services.llm import llm_status
from backend.processing.gpu_classifier import get_device_info

router = APIRouter()


@router.get("/dashboard/summary")
async def dashboard_summary(_: dict = Depends(get_current_user)) -> dict:
    jobs = get_job_store().list_jobs(limit=8)
    cv_report = None
    cv_path = Path("artifacts/eval_domain_models_cv.json")
    if cv_path.exists():
        cv_report = json.loads(cv_path.read_text(encoding="utf-8"))

    exploration = build_exploration_summary(project_id=None, commodity="ta")
    return {
        "health": {"status": "ok"},
        "recent_jobs": jobs,
        "copilot": llm_status(),
        "gpu": get_device_info(),
        "domain_cv": cv_report.get("models") if cv_report else None,
        "economics_preview": exploration.get("economics_preview"),
        "deposit": exploration.get("deposit"),
    }