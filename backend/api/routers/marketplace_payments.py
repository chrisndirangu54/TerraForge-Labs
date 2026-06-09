from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post('/marketplace/checkout')
async def checkout(payload: dict) -> dict:
    provider = payload.get('provider', 'stripe')
    return {'provider': provider, 'status': 'sandbox_ok', 'receipt_id': 'rcpt-001'}


@router.post('/marketplace/install')
async def install_plugin(payload: dict) -> dict:
    return {'installed': True, 'plugin_id': payload.get('plugin_id', 'aseg_gdf2'), 'new_endpoints': ['/parse-aseg-gdf2']}
