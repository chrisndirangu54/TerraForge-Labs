from __future__ import annotations


from backend.api.auth.router import mutating_router
from backend.api.jobs.enqueue import submit_job
from backend.api.tasks import celery_gpu_classification, run_gpu_classification
from shared.instruments.thin_section import classify_thin_section
from shared.instruments.xrd_bruker import parse_xrd

router = mutating_router()


@router.post("/classify-thin-section")
async def classify(payload: dict) -> dict:
    if payload.get("async"):
        return submit_job(
            job_type="gpu_classification",
            payload={
                "task": "grain_segmentation",
                "image_path": payload.get("ppl_path"),
                "project_id": payload.get("project_id"),
                "async": True,
            },
            runner=run_gpu_classification,
            celery_task=celery_gpu_classification,
            meta={"task": "grain_segmentation"},
            async_default=True,
            user={"id": "anonymous"},
        )
    return classify_thin_section(
        payload.get("ppl_path", "tests/fixtures/thin_sections/ppl_01.tif"),
        payload.get("xpl_path", "tests/fixtures/thin_sections/xpl_01.tif"),
    )


@router.post("/parse-xrd")
async def parse_xrd_route(payload: dict) -> dict:
    return parse_xrd(payload.get("filepath", "tests/fixtures/sample_xrd.raw"))
