from backend.processing.geothermal_resource import estimate_geothermal_resource
from backend.processing.inversion_3d_mt import run_mt3d_inversion


def test_mt3d_requires_min_sites():
    out = run_mt3d_inversion({'edi_upload_ids': ['a'] * 10})
    assert out['status'] == 'error'


def test_mt3d_with_sufficient_sites_and_resource():
    out = run_mt3d_inversion({'edi_upload_ids': ['a'] * 20})
    assert out['status'] == 'ok'
    resource = estimate_geothermal_resource(5.2, 245)
    assert resource['electrical_potential_MWe'] > 0
