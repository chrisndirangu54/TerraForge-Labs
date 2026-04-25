from __future__ import annotations

from fastapi import APIRouter

SEED_ITEMS = [
    {'name': 'ASEG-GDF2 parser plugin', 'price_usd': 0, 'category': 'plugin'},
    {'name': 'Geosoft .grd parser plugin', 'price_usd': 0, 'category': 'plugin'},
    {'name': 'NI 43-101 template', 'price_usd': 49, 'category': 'template'},
    {'name': 'USGS MRDS Kenya bundle', 'price_usd': 0, 'category': 'dataset'},
    {'name': 'Kenya EL progress template', 'price_usd': 29, 'category': 'template'},
]

router = APIRouter()


@router.get('/marketplace/catalogue')
async def catalogue() -> dict:
    return {'items': SEED_ITEMS, 'count': len(SEED_ITEMS)}
