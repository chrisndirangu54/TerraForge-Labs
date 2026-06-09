from __future__ import annotations

from fastapi import APIRouter

from backend.processing.tectonic_context import infer_tectonic_context

router = APIRouter()


@router.post('/tectonic-context')
async def tectonic_context(payload: dict) -> dict:
    return infer_tectonic_context(payload.get('bbox', [37.45, -1.2, 37.55, -1.1]))
