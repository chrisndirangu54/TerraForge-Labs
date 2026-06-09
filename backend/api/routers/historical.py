from __future__ import annotations

from fastapi import APIRouter

from backend.processing.ocr_borehole import extract_borehole_intervals

router = APIRouter()


@router.post('/ingest-historical')
async def ingest_historical(payload: dict) -> dict:
    if payload.get('source_type') == 'borehole_pdf':
        extracted = extract_borehole_intervals('sample ocr text')
        return {'status': 'ok', 'records_extracted': len(extracted['intervals']), 'data': extracted}
    return {'status': 'ok', 'message': 'format accepted (phase2 scaffold)'}
