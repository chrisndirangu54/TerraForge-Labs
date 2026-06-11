from fastapi.testclient import TestClient

from backend.api.main import app
from backend.processing.fusion_engine import compute_fusion_score

client = TestClient(app)


def test_fusion_engine_combines_source_scores():
    result = compute_fusion_score(
        {
            "geochemistry": 85,
            "geophysics": 70,
            "geobotany": 60,
            "structural": 55,
            "targets": [
                {"hole_id": "DH-1", "base_score": 90},
                {"hole_id": "DH-2", "base_score": 65},
            ],
        }
    )
    assert 0.0 < result["fusion_score"] <= 1.0
    assert (
        result["contributions"]["geochemistry"] > result["contributions"]["structural"]
    )
    assert result["ranked_targets"][0]["hole_id"] == "DH-1"


def test_fusion_score_endpoint():
    response = client.post(
        "/targeting/fusion-score",
        json={
            "geochemistry": 88,
            "geophysics": 72,
            "geobotany": 80,
            "structural": 50,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "fusion_score" in body
    assert body["classification"] in {"high_priority", "moderate", "low_priority"}
