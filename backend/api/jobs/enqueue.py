from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import Any

from backend.api.auth.projects import ensure_project_access
from backend.api.celery_app import celery_app
from backend.api.jobs.store import get_job_store

logger = logging.getLogger(__name__)

_broker_cache: tuple[bool, float] | None = None
_BROKER_CACHE_TTL = 30.0


def _invalidate_broker_cache() -> None:
    global _broker_cache
    _broker_cache = None


def celery_broker_available() -> bool:
    """Return True when async Celery dispatch is expected to succeed."""
    global _broker_cache

    now = time.monotonic()
    if _broker_cache is not None:
        available, cached_at = _broker_cache
        if now - cached_at < _BROKER_CACHE_TTL:
            return available

    if celery_app is None:
        _broker_cache = (False, now)
        return False

    if celery_app.conf.task_always_eager:
        _broker_cache = (True, now)
        return True

    broker_url = (
        celery_app.conf.get("broker_url")
        or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    try:
        import redis

        client = redis.Redis.from_url(
            broker_url,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        client.ping()
        available = True
    except Exception:
        available = False

    _broker_cache = (available, now)
    return available


def _dispatch_celery(celery_task: Any, job_id: str, payload: dict) -> bool:
    """Enqueue via Celery. Returns False when broker is unavailable."""
    try:
        celery_task.delay(job_id, payload)
        return True
    except Exception as exc:
        _invalidate_broker_cache()
        logger.warning(
            "Celery dispatch failed for job %s — falling back to sync execution: %s",
            job_id,
            exc,
        )
        return False


def submit_job(
    *,
    job_type: str,
    payload: dict,
    runner: Callable[[str, dict], dict],
    celery_task: Any | None,
    meta: dict[str, Any] | None = None,
    async_default: bool = True,
    user: dict | None = None,
) -> dict:
    project_id = payload.get("project_id")
    if user is not None:
        ensure_project_access(user, str(project_id) if project_id else None)

    job_id = str(uuid.uuid4())
    store = get_job_store()
    use_async = bool(payload.get("async", async_default))

    job_meta = {**(meta or {})}
    if project_id:
        job_meta["project_id"] = str(project_id)
    if user and user.get("id") != "anonymous":
        job_meta["created_by"] = user["id"]

    can_dispatch_async = (
        use_async
        and celery_app is not None
        and celery_task is not None
        and celery_broker_available()
    )

    store.set(
        job_id,
        {
            "job_type": job_type,
            "status": "queued" if can_dispatch_async else "running",
            **job_meta,
        },
    )

    run_payload = {**payload, "job_id": job_id}

    if can_dispatch_async:
        if _dispatch_celery(celery_task, job_id, run_payload):
            response: dict[str, Any] = {
                "job_id": job_id,
                "status": "queued",
                "job_type": job_type,
                "poll_url": f"/jobs/{job_id}",
            }
            response.update(job_meta)
            return response
        store.set(job_id, {"job_type": job_type, "status": "running", **job_meta})

    runner(job_id, run_payload)
    stored = store.get(job_id)
    return {"job_id": job_id, "poll_url": f"/jobs/{job_id}", **stored}