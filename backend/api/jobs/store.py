from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

_STORE: "JobStore | None" = None


class JobStore(ABC):
    @abstractmethod
    def set(self, job_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, job_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def append_event(
        self, job_id: str, status: str, meta: dict[str, Any] | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_jobs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        job_type: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError


def _backend_name() -> str:
    configured = os.getenv("JOB_STORE_BACKEND", "").lower()
    if configured:
        return configured
    from backend.api.db import db_available

    return "postgres" if db_available() else "memory"


def get_job_store() -> JobStore:
    global _STORE
    if _STORE is not None:
        return _STORE

    backend = _backend_name()
    if backend == "redis":
        from backend.api.jobs.redis_store import RedisJobStore

        _STORE = RedisJobStore()
    elif backend == "postgres":
        from backend.api.jobs.postgres_store import PostgresJobStore

        _STORE = PostgresJobStore()
    else:
        from backend.api.jobs.memory_store import MemoryJobStore

        _STORE = MemoryJobStore()
    return _STORE


def reset_job_store() -> None:
    global _STORE
    _STORE = None