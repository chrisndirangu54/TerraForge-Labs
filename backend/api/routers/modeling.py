from __future__ import annotations

import uuid

from fastapi import APIRouter

from backend.api.tasks import run_deposit_model

router = APIRouter()


@router.post("/deposit-model")
async def generate_deposit_model(payload: dict) -> dict:
    job_id = str(uuid.uuid4())
    run_deposit_model(job_id, payload)
    return {"job_id": job_id}
