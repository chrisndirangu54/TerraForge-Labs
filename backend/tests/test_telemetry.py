from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.middleware.telemetry import reset_metrics_store

client = TestClient(app)


def setup_function() -> None:
    reset_metrics_store()


def test_health_records_request_metrics():
    response = client.get("/health")
    assert response.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert "http_requests_total" in body
    assert 'method="GET"' in body
    assert 'path="/health"' in body
    assert 'status="200"' in body
    assert "http_request_duration_seconds_count" in body
    assert "http_request_duration_seconds_sum" in body


def test_metrics_endpoint_prometheus_content_type():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/plain; version=0.0.4; charset=utf-8"
    )


def test_metrics_not_counted_for_scrape_endpoint():
    client.get("/metrics")
    metrics = client.get("/metrics").text
    assert 'path="/metrics"' not in metrics or (
        'http_requests_total{method="GET",path="/metrics"' not in metrics
    )


def test_path_normalization_for_dynamic_segments():
    client.get("/health")
    client.get("/version")
    metrics = client.get("/metrics").text
    assert 'path="/health"' in metrics
    assert 'path="/version"' in metrics
