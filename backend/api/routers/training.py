from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.api.auth.dependencies import require_mutating_access
from backend.api.jobs.enqueue import submit_job
from backend.api.services.response_display import enrich_response
from backend.api.services.training_data_upload import (
    get_domain_eval_report,
    get_training_manifest,
    ingest_spectral_upload,
    ingest_thin_section_upload,
)
from backend.api.tasks import (
    celery_pull_datasets,
    celery_train_geobotany,
    celery_train_mineral,
    celery_train_spectral,
    celery_train_thin_section,
    pull_datasets,
    train_geobotany,
    train_mineral,
    train_spectral,
    train_thin_section,
)
from models.thin_section_classifier.dataset import THIN_SECTION_CLASSES
from shared.constants import MINERAL_CLASSES

router = APIRouter()


@router.get("/training/domain/eval")
async def training_domain_eval() -> dict:
    return enrich_response(get_domain_eval_report())


@router.get("/training/{task}/manifest")
async def training_manifest(task: str) -> dict:
    try:
        return enrich_response(get_training_manifest(task))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/training/{task}/classes")
async def training_classes(task: str) -> dict:
    normalized = task.lower()
    if normalized == "thin_section":
        return {"task": normalized, "classes": THIN_SECTION_CLASSES}
    if normalized == "spectral":
        return {"task": normalized, "classes": MINERAL_CLASSES}
    raise HTTPException(status_code=404, detail=f"Unknown training task: {task}")


@router.post(
    "/training/thin_section/upload",
    dependencies=[Depends(require_mutating_access)],
)
async def upload_thin_section_training_data(
    class_name: str = Form(...),
    project_id: str | None = Form(default=None),
    pair_file: UploadFile | None = File(default=None),
    ppl_file: UploadFile | None = File(default=None),
    xpl_file: UploadFile | None = File(default=None),
) -> dict:
    try:
        result = ingest_thin_section_upload(
            class_name=class_name,
            pair_bytes=await pair_file.read() if pair_file else None,
            pair_filename=pair_file.filename if pair_file else None,
            ppl_bytes=await ppl_file.read() if ppl_file else None,
            xpl_bytes=await xpl_file.read() if xpl_file else None,
            project_id=project_id,
        )
        return enrich_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/training/spectral/upload",
    dependencies=[Depends(require_mutating_access)],
)
async def upload_spectral_training_data(
    class_name: str = Form(...),
    project_id: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> dict:
    try:
        result = ingest_spectral_upload(
            class_name=class_name,
            file_bytes=await file.read(),
            filename=file.filename or "spectrum.npy",
            project_id=project_id,
        )
        return enrich_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/training/datasets/pull", dependencies=[Depends(require_mutating_access)])
async def pull_training_datasets(payload: dict | None = None) -> dict:
    body = payload or {}
    return submit_job(
        job_type="dataset_pull",
        payload=body,
        runner=pull_datasets,
        celery_task=celery_pull_datasets,
        async_default=bool(body.get("async", False)),
        meta={"pipeline": "dataset_pull"},
        user={"id": body.get("user_id", "system")},
    )


@router.post("/training/{task}/run", dependencies=[Depends(require_mutating_access)])
async def run_training(task: str, payload: dict | None = None) -> dict:
    body = payload or {}
    normalized = task.lower()
    if normalized == "mineral":
        return submit_job(
            job_type="mineral_train",
            payload=body,
            runner=train_mineral,
            celery_task=celery_train_mineral,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "mineral_train"},
            user={"id": body.get("user_id", "system")},
        )
    if normalized == "geobotany":
        return submit_job(
            job_type="geobotany_train",
            payload=body,
            runner=train_geobotany,
            celery_task=celery_train_geobotany,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "geobotany_train"},
            user={"id": body.get("user_id", "system")},
        )
    if normalized == "thin_section":
        return submit_job(
            job_type="thin_section_train",
            payload=body,
            runner=train_thin_section,
            celery_task=celery_train_thin_section,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "thin_section_train"},
            user={"id": body.get("user_id", "system")},
        )
    if normalized == "spectral":
        return submit_job(
            job_type="spectral_train",
            payload=body,
            runner=train_spectral,
            celery_task=celery_train_spectral,
            async_default=bool(body.get("async", True)),
            meta={"pipeline": "spectral_train"},
            user={"id": body.get("user_id", "system")},
        )
    raise HTTPException(status_code=404, detail=f"Unknown training task: {task}")