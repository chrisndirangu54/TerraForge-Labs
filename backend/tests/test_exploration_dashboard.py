from fastapi.testclient import TestClient

from backend.api.auth.repository import reset_auth_repository
from backend.api.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_auth_repository()


def _auth_headers() -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "email": "explore@example.com",
            "password": "securepass1",
            "role": "geologist",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "explore@example.com", "password": "securepass1"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_summary_returns_economics_and_jobs():
    headers = _auth_headers()
    response = client.get("/dashboard/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["health"]["status"] == "ok"
    assert "recent_jobs" in body
    assert "economics_preview" in body
    assert "deposit" in body
    assert "npv_usd" in body["economics_preview"]


def test_exploration_summary_includes_financial_payload():
    headers = _auth_headers()
    response = client.get("/projects/exploration-summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["commodity"] == "ta"
    assert "deposit" in body
    assert "economics_preview" in body
    payload = body["recommended_financial_payload"]
    assert payload["commodity"] == "ta"
    assert payload["ore_tonnes"] > 0
    assert payload["grade"] > 0


def test_deposit_summary_returns_block_preview():
    headers = _auth_headers()
    response = client.get("/deposit/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "ore_tonnes_estimate" in body
    assert "blocks_preview" in body


def test_field_catalog_lists_datasets():
    headers = _auth_headers()
    response = client.get("/ingest/field-catalog", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "catalogs" in body
    assert len(body["catalogs"]) >= 1
    names = {entry["name"] for entry in body["catalogs"]}
    assert "field_geochem" in names


def test_field_upload_register_creates_manifest(tmp_path, monkeypatch):
    import backend.api.services.field_data_catalog as catalog_mod

    monkeypatch.setattr(
        catalog_mod,
        "_repo_root",
        lambda: tmp_path,
    )
    headers = _auth_headers()
    response = client.post(
        "/ingest/field-upload/register",
        headers=headers,
        json={
            "dataset": "thin_section",
            "files": ["data/thin_section/manifest.json"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "registered"
    assert body["dataset"] == "thin_section"