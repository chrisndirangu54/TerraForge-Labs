import os

from fastapi.testclient import TestClient

from backend.api.auth.repository import reset_auth_repository
from backend.api.ingest.store import reset_ingest_store
from backend.api.jobs.store import reset_job_store
from backend.api.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_auth_repository()
    reset_ingest_store()
    reset_job_store()
    os.environ["AUTH_REQUIRED"] = "true"


def teardown_function() -> None:
    os.environ["AUTH_REQUIRED"] = "false"


def _register_and_login(email: str, role: str = "geologist") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": "securepass1", "role": role},
    )
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "securepass1"},
    )
    return login.json()["access_token"]


def _create_project(token: str, slug: str) -> dict:
    response = client.post(
        "/projects",
        json={"slug": slug, "name": slug},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()


def test_user_cannot_read_other_project_observations():
    token_a = _register_and_login("alice@example.com")
    token_b = _register_and_login("bob@example.com")
    project_a = _create_project(token_a, "project-a")

    ingest = client.post(
        "/ingest/observations",
        json={
            "observations": [
                {
                    "project_id": project_a["id"],
                    "source": "test",
                    "parser_version": "manual@1.0.0",
                    "crs": "EPSG:4326",
                    "instrument_type": "field_note",
                    "sample_id": "A-1",
                    "lon": 37.5,
                    "lat": -1.15,
                    "data": {"note": "secret"},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert ingest.status_code == 200

    denied = client.get(
        "/ingest/observations",
        params={"project_id": project_a["id"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied.status_code == 403

    scoped = client.get(
        "/ingest/observations",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert scoped.status_code == 200
    assert scoped.json()["count"] == 0


def test_user_cannot_ingest_into_foreign_project():
    token_a = _register_and_login("owner@example.com")
    token_b = _register_and_login("intruder@example.com")
    project_a = _create_project(token_a, "owner-project")

    response = client.post(
        "/ingest/observations",
        json={
            "observations": [
                {
                    "project_id": project_a["id"],
                    "source": "test",
                    "parser_version": "manual@1.0.0",
                    "crs": "EPSG:4326",
                    "instrument_type": "field_note",
                    "sample_id": "X-1",
                    "data": {"note": "blocked"},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


def test_jobs_are_scoped_by_project_membership():
    token_a = _register_and_login("jobs-a@example.com")
    token_b = _register_and_login("jobs-b@example.com")
    project_a = _create_project(token_a, "jobs-project-a")

    submitted = client.post(
        "/classification/gpu/sync",
        json={"task": "mineral", "project_id": project_a["id"], "async": False},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["job_id"]

    denied = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied.status_code == 403

    allowed = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["project_id"] == project_a["id"]
