from __future__ import annotations

from fastapi import APIRouter

from backend.api.services.audit_v2 import build_audit_event
from backend.api.services.jorc_v2 import generate_kenya_el_report, generate_ni43101_report

router = APIRouter()


@router.post('/reports/ni43101')
async def ni43101(payload: dict) -> dict:
    result = generate_ni43101_report(payload.get('project_name', 'Matuu Project'), payload)
    audit = build_audit_event({'action': 'generate_ni43101', 'resource_type': 'report', 'project': payload.get('project_name')})
    return {**result, 'audit_event': audit}


@router.post('/reports/kenya-el')
async def kenya_el(payload: dict) -> dict:
    result = generate_kenya_el_report(payload.get('project_name', 'Matuu Project'), payload)
    audit = build_audit_event({'action': 'generate_kenya_el', 'resource_type': 'report', 'project': payload.get('project_name')})
    return {**result, 'audit_event': audit}
