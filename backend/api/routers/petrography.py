from __future__ import annotations

from fastapi import APIRouter

from shared.instruments.thin_section import classify_thin_section
from shared.instruments.xrd_bruker import parse_xrd

router = APIRouter()


@router.post('/classify-thin-section')
async def classify(payload: dict) -> dict:
    return classify_thin_section(payload.get('ppl_path', 'tests/fixtures/thin_sections/ppl_01.tif'), payload.get('xpl_path', 'tests/fixtures/thin_sections/xpl_01.tif'))


@router.post('/parse-xrd')
async def parse_xrd_route(payload: dict) -> dict:
    return parse_xrd(payload.get('filepath', 'tests/fixtures/sample_xrd.raw'))
