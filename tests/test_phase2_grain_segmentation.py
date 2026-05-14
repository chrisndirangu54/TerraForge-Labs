from models.grain_segmentation.dataset import get_dataset_manifest
from models.grain_segmentation.evaluate import evaluate_grain_model_stub
from models.grain_segmentation.train import train_grain_segmentation_stub


def test_grain_segmentation_stub_training():
    out = train_grain_segmentation_stub(epochs=2)
    assert out['history'][1] < out['history'][0]


def test_grain_segmentation_manifest_and_eval():
    manifest = get_dataset_manifest()
    eval_out = evaluate_grain_model_stub()
    assert manifest['pairs_expected'] == 20
    assert eval_out['mean_iou'] >= 0.75
