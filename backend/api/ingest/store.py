from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from shared.schemas.observation import ObservationRecord

_STORE: "IngestStore | None" = None


class IngestStore(ABC):
    @abstractmethod
    def insert_observations(self, observations: list[ObservationRecord]) -> int:
        raise NotImplementedError

    @abstractmethod
    def list_observations(
        self,
        *,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class MemoryIngestStore(IngestStore):
    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []

    def insert_observations(self, observations: list[ObservationRecord]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        for obs in observations:
            self._rows.append(
                {
                    "id": str(uuid.uuid4()),
                    "upload_id": obs.upload_id,
                    "project_id": obs.project_id,
                    "source": obs.source,
                    "parser_version": obs.parser_version,
                    "crs": obs.crs,
                    "instrument_type": obs.instrument_type,
                    "sample_id": obs.sample_id,
                    "lon": obs.lon,
                    "lat": obs.lat,
                    "data": obs.data,
                    "flagged": obs.flagged,
                    "flag_reasons": obs.flag_reasons,
                    "uploaded_at": now,
                }
            )
        return len(observations)

    def list_observations(
        self,
        *,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        items = self._rows
        if project_id:
            items = [row for row in items if row["project_id"] == project_id]
        return items[offset : offset + limit]


class PostgresIngestStore(IngestStore):
    def insert_observations(self, observations: list[ObservationRecord]) -> int:
        if not observations:
            return 0
        from backend.api.db import get_connection

        with get_connection() as conn:
            for obs in observations:
                upload_id = obs.upload_id or str(uuid.uuid4())
                params: list[Any] = [
                    upload_id,
                    obs.project_id,
                    obs.source,
                    obs.parser_version,
                    obs.crs,
                    obs.instrument_type,
                    obs.sample_id,
                ]
                if obs.lon is not None and obs.lat is not None:
                    geom_sql = "ST_SetSRID(ST_MakePoint(%s, %s), 4326)"
                    params.extend([obs.lon, obs.lat])
                else:
                    geom_sql = "NULL"
                params.extend([json.dumps(obs.data), obs.flagged, obs.flag_reasons])

                conn.execute(
                    f"""
                    INSERT INTO instrument_readings (
                        upload_id, project_id, source, parser_version, crs,
                        instrument_type, sample_id, geom, data, flagged, flag_reasons
                    )
                    VALUES (
                        %s::uuid, %s::uuid, %s, %s, %s,
                        %s, %s, {geom_sql}, %s::jsonb, %s, %s
                    )
                    """,
                    params,
                )
            conn.commit()
        return len(observations)

    def list_observations(
        self,
        *,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        from backend.api.db import get_connection

        clauses = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = %s::uuid")
            params.append(project_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        query = f"""
            SELECT
                id, upload_id, project_id, source, parser_version, crs,
                instrument_type, sample_id,
                ST_X(geom) AS lon, ST_Y(geom) AS lat,
                data, flagged, flag_reasons, uploaded_at
            FROM instrument_readings
            {where}
            ORDER BY uploaded_at DESC
            LIMIT %s OFFSET %s
        """
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            data = row.get("data") or {}
            if isinstance(data, str):
                data = json.loads(data)
            items.append(
                {
                    "id": str(row["id"]),
                    "upload_id": str(row["upload_id"]),
                    "project_id": str(row["project_id"]) if row["project_id"] else None,
                    "source": row["source"],
                    "parser_version": row["parser_version"],
                    "crs": row["crs"],
                    "instrument_type": row["instrument_type"],
                    "sample_id": row["sample_id"],
                    "lon": row.get("lon"),
                    "lat": row.get("lat"),
                    "data": data,
                    "flagged": row["flagged"],
                    "flag_reasons": row.get("flag_reasons") or [],
                    "uploaded_at": (
                        row["uploaded_at"].isoformat() if row["uploaded_at"] else None
                    ),
                }
            )
        return items


def _backend_name() -> str:
    configured = os.getenv("INGEST_STORE_BACKEND", "").lower()
    if configured:
        return configured
    from backend.api.db import db_available

    return "postgres" if db_available() else "memory"


def get_ingest_store() -> IngestStore:
    global _STORE
    if _STORE is not None:
        return _STORE

    backend = _backend_name()
    if backend == "postgres":
        _STORE = PostgresIngestStore()
    else:
        _STORE = MemoryIngestStore()
    return _STORE


def reset_ingest_store() -> None:
    global _STORE
    _STORE = None
