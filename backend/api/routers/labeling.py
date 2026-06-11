from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.services.labeling_store import get_labeling_store

router = APIRouter()


@router.get("/labeling/queue")
async def list_label_queue(status: str | None = None) -> dict:
    items = get_labeling_store().list_items(status=status)
    return {"count": len(items), "items": items}


@router.post("/labeling/queue")
async def enqueue_label(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    item = get_labeling_store().enqueue(
        {**payload, "actor": user.get("email", user.get("id"))}
    )
    return item


@router.post("/labeling/queue/{item_id}/confirm")
async def confirm_label(
    item_id: str,
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    confirmed_label = payload.get("confirmed_label") or payload.get("species")
    if not confirmed_label:
        raise HTTPException(status_code=400, detail="confirmed_label is required")
    try:
        return get_labeling_store().confirm(item_id, str(confirmed_label))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/labeling/queue/{item_id}")
async def delete_label(
    item_id: str,
    user: dict = Depends(require_mutating_access),
) -> dict:
    deleted = get_labeling_store().delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Label queue item not found")
    return {"deleted": True, "id": item_id}
