from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)

EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "0",
    "referrer-policy": "strict-origin-when-cross-origin",
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "permissions-policy": "geolocation=(), microphone=(), camera=()",
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
}


def test_security_headers_on_health():
    response = client.get("/health")
    assert response.status_code == 200
    for header, value in EXPECTED_HEADERS.items():
        assert response.headers.get(header) == value, f"missing or wrong {header}"


def test_security_headers_on_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    for header, value in EXPECTED_HEADERS.items():
        assert response.headers.get(header) == value
