"""Prometheus metrics exposition endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Response

from backend.api.middleware.telemetry import metrics_store

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Return in-memory request metrics in Prometheus text format."""
    body = metrics_store.prometheus_text()
    return Response(
        content=body,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
