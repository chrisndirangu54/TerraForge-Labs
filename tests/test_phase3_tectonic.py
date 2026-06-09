from backend.processing.tectonic_context import infer_tectonic_context


def test_tectonic_context_scores():
    out = infer_tectonic_context([37.45, -1.2, 37.55, -1.1])
    assert out['deposit_type_scores']['orogenic_gold'] >= 80
