from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import get_current_user, require_roles
from backend.ml.registry import SUPPORTED_TASKS, get_model_registry

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/{task}/versions")
async def list_model_versions(
    task: str,
    _: dict = Depends(get_current_user),
) -> dict:
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task}")
    registry = get_model_registry()
    versions = registry.list_versions(task)
    production = registry.get_production(task)
    return {
        "task": task,
        "production_version": production["version"] if production else None,
        "versions": versions,
    }


@router.get("/{task}/production")
async def get_production_model(
    task: str,
    _: dict = Depends(get_current_user),
) -> dict:
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task}")
    production = get_model_registry().get_production(task)
    if production is None:
        raise HTTPException(status_code=404, detail="No production model registered")
    return production


@router.post("/{task}/versions/{version}/promote")
async def promote_model_version(
    task: str,
    version: str,
    payload: dict,
    _: dict = Depends(require_roles("admin", "geologist")),
) -> dict:
    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task}")

    stage = payload.get("stage", "production")
    if stage not in {"staging", "production"}:
        raise HTTPException(status_code=400, detail="stage must be staging or production")

    registry = get_model_registry()
    try:
        record = registry.promote(task, version, stage=stage)  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return record