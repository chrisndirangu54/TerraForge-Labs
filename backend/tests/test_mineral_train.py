from pathlib import Path

from models.mineral_classifier.convert_tflite import export_metadata
from models.mineral_classifier.dataset import generate_synthetic_dataset
from models.mineral_classifier.evaluate import evaluate_mineral_classifier
from models.mineral_classifier.infer import classify_mineral
from models.mineral_classifier.train import train_mineral_classifier
from shared.constants import MIN_CLASSIFICATION_ACCURACY


def test_synthetic_dataset_has_expected_classes():
    x, y, classes = generate_synthetic_dataset(n_samples_per_class=8, seed=1)
    assert x.shape[0] == len(y)
    assert len(classes) == 8
    assert set(y.tolist()) <= set(range(len(classes)))


def test_train_saves_checkpoint(tmp_path):
    checkpoint = tmp_path / "mineral_checkpoint.json"
    result = train_mineral_classifier(
        epochs=3,
        samples_per_class=12,
        checkpoint_path=checkpoint,
    )
    assert checkpoint.exists()
    assert result["checkpoint_path"] == str(checkpoint)
    assert result["feature_dim"] == 32


def test_evaluate_meets_accuracy_threshold(tmp_path):
    checkpoint = tmp_path / "mineral_checkpoint.json"
    train_mineral_classifier(samples_per_class=20, checkpoint_path=checkpoint)
    metrics = evaluate_mineral_classifier(checkpoint_path=checkpoint, seed=77)
    assert metrics["accuracy"] >= MIN_CLASSIFICATION_ACCURACY
    assert metrics["meets_threshold"] is True


def test_infer_loads_checkpoint_and_classifies(tmp_path):
    checkpoint = tmp_path / "mineral_checkpoint.json"
    train_mineral_classifier(samples_per_class=16, checkpoint_path=checkpoint)
    result = classify_mineral(
        {"image_base64": "abc123", "project_id": "matuu"},
        checkpoint_path=checkpoint,
    )
    assert "label" in result
    assert result["confidence"] > 0
    assert len(result["top3"]) == 3


def test_convert_tflite_exports_metadata(tmp_path):
    checkpoint = tmp_path / "mineral_checkpoint.json"
    train_mineral_classifier(samples_per_class=10, checkpoint_path=checkpoint)
    metadata_path = tmp_path / "export_metadata.json"
    metadata = export_metadata(
        checkpoint_path=checkpoint,
        output_path=metadata_path,
    )
    assert metadata_path.exists()
    assert metadata["model_name"] == "mineral_classifier"
    assert metadata["classes"]
    assert Path(metadata["metadata_path"]).exists()
