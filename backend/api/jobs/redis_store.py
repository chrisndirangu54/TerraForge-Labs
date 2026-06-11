from __future__ import annotations

import json
import os
from typing import Any

import redis

from backend.api.jobs.postgres_store import PostgresJobStore
from backend.api.jobs.store import JobStore


class RedisJobStore(JobStore):
    """Redis cache in front of Postgres for hot job reads."""

    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = redis.from_url(url, decode_responses=True)
        self._postgres = PostgresJobStore()
        self._ttl = int(os.getenv("JOB_CACHE_TTL_SECONDS", "3600"))

    def _cache_key(self, job_id: str) -> str:
        return f"terraforge:job:{job_id}"

    def set(self, job_id: str, data: dict[str, Any]) -> None:
        self._postgres.set(job_id, data)
        cached = self._postgres.get(job_id)
        self._redis.setex(self._cache_key(job_id), self._ttl, json.dumps(cached))

    def get(self, job_id: str) -> dict[str, Any]:
        cached = self._redis.get(self._cache_key(job_id))
        if cached:
            return json.loads(cached)
        data = self._postgres.get(job_id)
        if data.get("status") != "pending":
            self._redis.setex(self._cache_key(job_id), self._ttl, json.dumps(data))
        return data

    def append_event(
        self, job_id: str, status: str, meta: dict[str, Any] | None = None
    ) -> None:
        self._postgres.append_event(job_id, status, meta)
        self._redis.delete(self._cache_key(job_id))

    def list_jobs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        job_type: str | None = None,
        project_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return self._postgres.list_jobs(
            limit=limit,
            offset=offset,
            status=status,
            job_type=job_type,
            project_ids=project_ids,
        )

    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        return self._postgres.get_events(job_id)
