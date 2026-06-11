from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.api.jobs.store import JobStore


class MemoryJobStore(JobStore):
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}

    def set(self, job_id: str, data: dict[str, Any]) -> None:
        current = self._jobs.get(job_id, {})
        merged = {**current, **data}
        self._jobs[job_id] = merged
        if "status" in data:
            self.append_event(job_id, data["status"], meta=data)

    def get(self, job_id: str) -> dict[str, Any]:
        return self._jobs.get(job_id, {"status": "pending"})

    def append_event(
        self, job_id: str, status: str, meta: dict[str, Any] | None = None
    ) -> None:
        event = {
            "status": status,
            "meta": meta or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._events.setdefault(job_id, []).append(event)

    def list_jobs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        job_type: str | None = None,
    ) -> list[dict[str, Any]]:
        items = []
        for job_id, job in self._jobs.items():
            if status and job.get("status") != status:
                continue
            if job_type and job.get("job_type") != job_type:
                continue
            items.append({"job_id": job_id, **job})
        items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return items[offset : offset + limit]

    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        return list(self._events.get(job_id, []))
