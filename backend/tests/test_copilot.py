from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.services.llm import rag_query

client = TestClient(app)


def test_rag_query_enforces_citations():
    result = rag_query(
        "What JORC sampling controls are required before approval?",
        {"project_id": "matuu"},
    )
    assert result["citation_count"] >= 1
    assert result["citations"][0]["source"]
    assert "JORC" in result["answer"] or "jorc" in result["answer"].lower()


def test_copilot_endpoints_return_cited_answers():
    response = client.post(
        "/copilot/query",
        json={
            "query": "Explain kriging uncertainty for drill spacing.",
            "project_id": "matuu",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert body["answer"]

    explain = client.post(
        "/copilot/explain-anomaly",
        json={"anomaly_type": "geobotany", "score": 82, "project_id": "matuu"},
    )
    assert explain.status_code == 200
    assert explain.json()["citation_count"] >= 1
