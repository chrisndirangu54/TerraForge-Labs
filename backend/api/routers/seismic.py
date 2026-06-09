from __future__ import annotations

from fastapi import APIRouter

from backend.processing.gravity_reduction import run_gravity_reduction
from backend.processing.inversion_2d import run_inversion_2d
from backend.processing.inversion_mt import run_mt_inversion

router = APIRouter()


@router.post('/fuse-seismic')
async def fuse_seismic(payload: dict) -> dict:
    inversion_type = payload.get('inversion_type', '2d')
    if payload.get('data_type') == 'gravity':
        g = run_gravity_reduction(payload)
        return {**g, 'job_id': 'gravity-job-1'}
    if payload.get('data_type') == 'mt':
        mt = run_mt_inversion(payload)
        return {**mt, 'job_id': 'mt-job-1'}
    inv = run_inversion_2d(payload) if inversion_type == '2d' else {'status': '1d-not-implemented'}
    return {**inv, 'job_id': 'seismic-job-1', 'velocity_model_url': 'minio://seismic/velocity_model.tif'}
