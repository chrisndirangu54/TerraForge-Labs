from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from backend.api.celery_app import celery_app
from backend.api.jobs.store import get_job_store


def submit_job(
    *,
    job_type: str,
    payload: dict,
    runner: Callable[[str, dict], dict],
    celery_task: Any | None,
    meta: dict[str, Any] | None = None,
    async_default: bool = True,
) -> dict:
    job_id = str(uuid.uuid4())
    store = get_job_store()
    use_async = bool(payload.get("async", async_default))

    if use_async and celery_app is not None and celery_task is not None:
        store.set(
            job_id,
            {
                "job_type": job_type,
                "status": "queued",
                **(meta or {}),
            },
        )
        celery_task.delay(job_id, payload)
        response: dict[str, Any] = {
            "job_id": job_id,
            "status": "queued",
            "job_type": job_type,
            "poll_url": f"/jobs/{job_id}",
        }
        response.update(meta or {})
        return response

    runner(job_id, payload)
    stored = store.get(job_id)
    return {"job_id": job_id, **stored}
