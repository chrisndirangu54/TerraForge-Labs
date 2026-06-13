from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from backend.api.auth.dependencies import get_current_user, require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.services.exploration_summary import _artifacts_dir, build_deposit_summary_response
from backend.api.services.response_display import enrich_response
from backend.api.services.storage import get_storage_service
from backend.api.tasks import celery_run_deposit_model, run_deposit_model

router = APIRouter()

_BASE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@router.get("/deposit/summary")
async def deposit_summary(
    project_id: str | None = Query(default=None),
    _: dict = Depends(get_current_user),
) -> dict:
    return enrich_response(build_deposit_summary_response(project_id=project_id))


@router.get("/deposit/mesh")
async def deposit_mesh(
    base: str = Query(default="deposit_model"),
    _: dict = Depends(get_current_user),
) -> Response:
    if not _BASE_NAME_RE.fullmatch(base):
        raise HTTPException(status_code=400, detail="Invalid mesh base name")

    storage = get_storage_service()
    key = f"models/{base}.obj"
    content = storage.get(key)
    if content is None:
        path = _artifacts_dir() / f"{base}.obj"
        if path.exists():
            content = path.read_bytes()

    if content is None:
        raise HTTPException(status_code=404, detail="Deposit mesh not found")

    return Response(content=content, media_type="model/obj")


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