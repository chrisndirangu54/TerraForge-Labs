from __future__ import annotations

from fastapi import APIRouter

from backend.processing.paleontology import fossil_occurrences, heritage_risk

router = APIRouter()


@router.get('/paleontology/occurrences')
async def occurrences(bbox: str = '') -> dict:
    _ = bbox
    return fossil_occurrences([35.0, 2.0, 37.0, 4.0])


@router.post('/paleontology/compliance-check')
async def compliance_check(payload: dict) -> dict:
    return heritage_risk(payload.get('polygon', {}))
