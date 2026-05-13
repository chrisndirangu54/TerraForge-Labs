from __future__ import annotations

import uuid

from fastapi import APIRouter

from backend.api.tasks import generate_jorc_report

router = APIRouter()


@router.post("/reports/jorc")
async def generate_jorc(payload: dict) -> dict:
    job_id = str(uuid.uuid4())
    generate_jorc_report(job_id, payload)
    return {"job_id": job_id}
