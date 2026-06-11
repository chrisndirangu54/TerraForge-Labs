from fastapi.testclient import TestClient

from backend.api.auth.repository import reset_auth_repository
from backend.api.main import app
from backend.ml.registry import get_model_registry, reset_model_registry
from backend.processing.gpu_classifier import classify_gpu
from models.mineral_classifier.evaluate import evaluate_stub
from models.mineral_classifier.train import train_stub

client = TestClient(app)


def setup_function() -> None:
    reset_model_registry()
    reset_auth_repository()


def test_registry_lists_and_promotes_versions():
    registry = get_model_registry()
    production = registry.get_production("mineral")
    assert production is not None
    assert production["stage"] == "production"

    train_record = train_stub(epochs=2, samples=8)
    assert train_record["version"]
    assert train_record["stage"] == "staging"

    eval_record = evaluate_stub()
    assert eval_record["accuracy"] == 0.86
    assert eval_record["stage"] == "staging"

    promoted = registry.promote("mineral", eval_record["version"], stage="production")
    assert promoted["stage"] == "production"
    assert registry.get_production("mineral")["version"] == eval_record["version"]


def test_gpu_classifier_uses_production_registry_version():
    registry = get_model_registry()
    version = "v-test-production"
    registry.register_version(
        "mineral",
        version=version,
        params={"backbone": "torchvision-resnet18", "feature_dim": 512},
        metrics={"accuracy": 0.91},
        stage="production",
    )

    result = classify_gpu("mineral", {"project_id": "demo"})
    assert result["model_version"] == version
    assert result["registry_artifact"]


def test_models_api_lists_versions():
    client.post(
        "/auth/register",
        json={
            "email": "ml@example.com",
            "password": "securepass1",
            "role": "geologist",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "ml@example.com", "password": "securepass1"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/models/mineral/versions", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["task"] == "mineral"
    assert body["production_version"]
    assert len(body["versions"]) >= 1
