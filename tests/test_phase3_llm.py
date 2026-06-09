from models.terraforge_geo_llm.evaluate import benchmark_stub
from models.terraforge_geo_llm.train import train_terraforge_geo_stub


def test_geo_llm_stub_targets():
    train = train_terraforge_geo_stub()
    eval_out = benchmark_stub()
    assert train['jorc_completeness'] >= 0.90
    assert eval_out['terraforge_geo_completeness'] > eval_out['gemini_flash_completeness']
