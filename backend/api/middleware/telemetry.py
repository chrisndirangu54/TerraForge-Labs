"""Request timing telemetry with in-memory Prometheus-compatible metrics."""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_NUMERIC_SEGMENT_RE = re.compile(r"/\d+(?=/|$)")


def normalize_path(path: str) -> str:
    """Collapse volatile path segments for stable metric labels."""
    normalized = _UUID_RE.sub("{id}", path)
    normalized = _NUMERIC_SEGMENT_RE.sub("/{id}", normalized)
    return normalized


class MetricsStore:
    """Thread-safe in-memory counter and latency summary store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.request_counts: dict[tuple[str, str, str], int] = defaultdict(int)
        self.duration_sums: dict[tuple[str, str], float] = defaultdict(float)
        self.duration_counts: dict[tuple[str, str], int] = defaultdict(int)

    def record(
        self, method: str, path: str, status_code: int, duration_s: float
    ) -> None:
        route = normalize_path(path)
        status = str(status_code)
        with self._lock:
            self.request_counts[(method, route, status)] += 1
            self.duration_sums[(method, route)] += duration_s
            self.duration_counts[(method, route)] += 1

    def reset(self) -> None:
        with self._lock:
            self.request_counts.clear()
            self.duration_sums.clear()
            self.duration_counts.clear()

    def prometheus_text(self) -> str:
        lines: list[str] = [
            "# HELP http_requests_total Total HTTP requests processed by the API.",
            "# TYPE http_requests_total counter",
        ]
        with self._lock:
            for (method, route, status), count in sorted(self.request_counts.items()):
                lines.append(
                    f'http_requests_total{{method="{method}",path="{route}",status="{status}"}} {count}'
                )

            lines.extend(
                [
                    "",
                    "# HELP http_request_duration_seconds HTTP request latency in seconds.",
                    "# TYPE http_request_duration_seconds summary",
                ]
            )
            for (method, route), total in sorted(self.duration_sums.items()):
                count = self.duration_counts[(method, route)]
                lines.append(
                    f'http_request_duration_seconds_count{{method="{method}",path="{route}"}} {count}'
                )
                lines.append(
                    f'http_request_duration_seconds_sum{{method="{method}",path="{route}"}} {total:.6f}'
                )

        return "\n".join(lines) + "\n"


metrics_store = MetricsStore()


def reset_metrics_store() -> None:
    """Clear all recorded metrics (used in tests)."""
    metrics_store.reset()


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Record per-request counters and latency summaries."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        metrics_store.record(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_s=elapsed,
        )
        return response
