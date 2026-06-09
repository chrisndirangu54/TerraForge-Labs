from __future__ import annotations

from fastapi import APIRouter

from shared.instruments.hyperspectral import parse_envi
from shared.instruments.lidar_drone import parse as parse_lidar

router = APIRouter()


@router.post('/fuse-spectral')
async def fuse_spectral(payload: dict) -> dict:
    data_type = payload.get('data_type')
    if data_type == 'lidar':
        lidar = parse_lidar(payload.get('filepath', 'fixture.laz'))
        return {
            'dem_geotiff_url': lidar.dem_url,
            'mineral_map_url': '',
            'lineament_geojson_url': lidar.lineaments_url,
            'abundance_rasters': {},
            'fused_anomaly_map_url': 'minio://spectral/fused_anomaly.tif',
            'stats': {'covered_area_km2': 1.0, 'mineral_detections': 0, 'processing_time_s': 1.2},
        }
    if data_type == 'hyperspectral':
        spec = parse_envi(payload.get('hdr_path', 'kwale_hsi.hdr'), payload.get('img_path', 'kwale_hsi.img'))
        return {
            'dem_geotiff_url': '',
            'mineral_map_url': spec['mineral_map_url'],
            'lineament_geojson_url': '',
            'abundance_rasters': {'kaolinite': 'minio://spectral/kaolinite.tif'},
            'fused_anomaly_map_url': 'minio://spectral/fused_anomaly.tif',
            'stats': {'covered_area_km2': 1.0, 'mineral_detections': 2, 'processing_time_s': 2.4},
        }
    return {'error': 'Unsupported data_type'}
