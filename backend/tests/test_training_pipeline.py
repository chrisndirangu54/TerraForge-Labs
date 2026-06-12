from scripts.datasets.pull_field_data import pull_field_datasets

from models.mineral_classifier.train import train_mineral_classifier


def test_pull_field_datasets_copies_matuu_fixture():
    result = pull_field_datasets()
    assert "matuu_synthetic.geojson" in result["files"]


def test_train_mineral_classifier_on_real_matuu_data():
    pull_field_datasets()
    result = train_mineral_classifier(epochs=2, data_source="real")
    assert result["samples"] >= 10
    assert result["checkpoint_path"]