from fastapi import APIRouter

from backend.api.tasks import JOB_STORE

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    item = JOB_STORE.get(job_id, {"status": "pending"})
    return {"job_id": job_id, **item}
