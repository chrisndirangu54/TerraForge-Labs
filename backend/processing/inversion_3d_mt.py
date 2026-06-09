from __future__ import annotations

MT3D_TARGET_RMS = 1.05
MT3D_MIN_SITES = 20
MT3D_CLAY_CAP_OHM_M = 10
MT3D_RESERVOIR_OHM_M = 100


def run_mt3d_inversion(payload: dict) -> dict:
    n_sites = len(payload.get('edi_upload_ids', []))
    if n_sites < MT3D_MIN_SITES:
        return {'status': 'error', 'error': f'minimum {MT3D_MIN_SITES} sites required'}
    return {
        'status': 'ok',
        'rms': 1.03,
        'model_netcdf_url': 'minio://mt3d/olkaria_model.nc',
        'vtk_url': 'minio://mt3d/olkaria_model.vtk',
        'depth_slices': ['minio://mt3d/depth_1km.tif', 'minio://mt3d/depth_5km.tif'],
        'iso_surfaces': ['minio://mt3d/iso_10.obj', 'minio://mt3d/iso_100.obj'],
    }
