from backend.processing.sem_automineralogy import run_sem_automineralogy


def test_sem_pipeline_stub_metrics():
    out = run_sem_automineralogy({})
    assert out['segmentation_iou'] >= 0.70
    assert out['phase_accuracy'] >= 0.85
