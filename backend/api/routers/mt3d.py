from __future__ import annotations

from fastapi import APIRouter

from backend.processing.geothermal_resource import estimate_geothermal_resource
from backend.processing.inversion_3d_mt import run_mt3d_inversion

router = APIRouter()


@router.post('/invert-mt-3d')
async def invert_mt_3d(payload: dict) -> dict:
    inv = run_mt3d_inversion(payload)
    if inv.get('status') != 'ok':
        return inv
    resource = estimate_geothermal_resource(5.2, 245)
    return {**inv, 'resource_estimate': resource, 'job_id': 'mt3d-job-1'}
