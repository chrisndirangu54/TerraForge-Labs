from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.labeling_store import reset_labeling_store
from backend.processing.geobotany_active_learning import (
    queue_low_confidence_observation,
)
from models.geobotany_classifier.evaluate import evaluate_geobotany_classifier
from models.geobotany_classifier.infer import classify_plant
from models.geobotany_classifier.train import train_geobotany_classifier

client = TestClient(app)


def test_geobotany_train_eval_and_infer_meets_threshold(tmp_path):
    checkpoint = tmp_path / "geobotany_checkpoint.json"
    train_geobotany_classifier(samples_per_class=18, checkpoint_path=checkpoint)
    metrics = evaluate_geobotany_classifier(checkpoint_path=checkpoint, seed=55)
    assert metrics["top1_accuracy"] >= 0.80
    result = classify_plant(
        payload={"image_base64": "plant-photo"}, checkpoint_path=checkpoint
    )
    assert "species" in result
    assert result["top3"]


def test_low_confidence_observation_is_queued():
    reset_labeling_store()
    queued = queue_low_confidence_observation(
        {
            "species": "unknown_vegetation",
            "confidence": 0.42,
            "lon": 37.5,
            "lat": -1.15,
            "project_id": "matuu",
        }
    )
    assert queued is not None
    assert queued["status"] == "queued"


def test_geobotany_router_uses_infer_and_queues_low_confidence():
    reset_labeling_store()
    response = client.post(
        "/geobotany/classify-plant",
        json={
            "image_base64": "low-confidence-image",
            "lon": 37.48,
            "lat": -1.15,
            "project_id": "matuu",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "species" in body
    assert "confidence" in body
    if body["confidence"] < 0.65:
        assert body["active_learning_queue_id"] is not None
