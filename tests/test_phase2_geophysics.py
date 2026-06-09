from backend.processing.gravity_reduction import run_gravity_reduction
from backend.processing.inversion_2d import run_inversion_2d
from backend.processing.inversion_mt import run_mt_inversion


def test_inversion_2d_outputs_depth_estimate():
    out = run_inversion_2d({'observations': [1, 2, 3]})
    assert out['depth_to_target_m'] > 0


def test_gravity_and_mt_scaffolds_return_urls():
    g = run_gravity_reduction({})
    mt = run_mt_inversion({})
    assert g['bouguer_anomaly_url'].startswith('minio://')
    assert mt['mt_profile_url'].startswith('minio://')
