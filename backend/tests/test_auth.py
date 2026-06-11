from fastapi.testclient import TestClient

from backend.api.auth.repository import reset_auth_repository
from backend.api.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_auth_repository()


def test_register_and_login():
    register = client.post(
        "/auth/register",
        json={
            "email": "geo@example.com",
            "password": "securepass1",
            "display_name": "Geo User",
            "role": "geologist",
        },
    )
    assert register.status_code == 200
    body = register.json()
    assert body["email"] == "geo@example.com"
    assert body["role"] == "geologist"

    login = client.post(
        "/auth/login",
        json={"email": "geo@example.com", "password": "securepass1"},
    )
    assert login.status_code == 200
    token_body = login.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "geo@example.com"


def test_create_project_with_auth():
    client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "securepass1",
            "role": "admin",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "securepass1"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/projects",
        json={"slug": "kitui-ta", "name": "Kitui Ta Project"},
        headers=headers,
    )
    assert created.status_code == 200
    project = created.json()
    assert project["slug"] == "kitui-ta"

    listed = client.get("/projects", headers=headers)
    assert listed.status_code == 200
    assert any(item["slug"] == "kitui-ta" for item in listed.json())


def test_anonymous_me_when_auth_not_required():
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == "anonymous"
