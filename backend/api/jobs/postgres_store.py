from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.api.db import get_connection
from backend.api.jobs.store import JobStore


class PostgresJobStore(JobStore):
    def set(self, job_id: str, data: dict[str, Any]) -> None:
        status = data.get("status", "pending")
        result = data.get("result")
        meta = {k: v for k, v in data.items() if k not in {"status", "result"}}
        now = datetime.now(timezone.utc)

        project_id = meta.pop("project_id", None) or data.get("project_id")
        created_by = meta.pop("created_by", None) or data.get("created_by")

        with get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM jobs WHERE id = %s::uuid",
                (job_id,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO jobs (
                        id, job_type, status, result, meta, project_id, created_by, updated_at
                    )
                    VALUES (%s::uuid, %s, %s, %s::jsonb, %s::jsonb, %s::uuid, %s::uuid, %s)
                    """,
                    (
                        job_id,
                        data.get("job_type", "generic"),
                        status,
                        json.dumps(result) if result is not None else None,
                        json.dumps(meta),
                        project_id,
                        created_by,
                        now,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = %s,
                        result = COALESCE(%s::jsonb, result),
                        meta = COALESCE(meta, '{}'::jsonb) || %s::jsonb,
                        project_id = COALESCE(%s::uuid, project_id),
                        created_by = COALESCE(%s::uuid, created_by),
                        updated_at = %s
                    WHERE id = %s::uuid
                    """,
                    (
                        status,
                        json.dumps(result) if result is not None else None,
                        json.dumps(meta),
                        project_id,
                        created_by,
                        now,
                        job_id,
                    ),
                )
            conn.execute(
                """
                INSERT INTO job_events (job_id, status, meta)
                VALUES (%s::uuid, %s, %s::jsonb)
                """,
                (job_id, status, json.dumps(meta)),
            )
            conn.commit()

    def get(self, job_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT job_type, status, result, meta, project_id, created_by,
                       created_at, updated_at
                FROM jobs WHERE id = %s::uuid
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return {"status": "pending"}
        meta = row.get("meta") or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        result = row.get("result")
        if isinstance(result, str):
            result = json.loads(result)
        payload = {
            "job_type": row["job_type"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "project_id": (
                str(row["project_id"]) if row.get("project_id") is not None else None
            ),
            "created_by": (
                str(row["created_by"]) if row.get("created_by") is not None else None
            ),
            **meta,
        }
        if result is not None:
            payload["result"] = result
        return payload

    def append_event(
        self, job_id: str, status: str, meta: dict[str, Any] | None = None
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO job_events (job_id, status, meta)
                VALUES (%s::uuid, %s, %s::jsonb)
                """,
                (job_id, status, json.dumps(meta or {})),
            )
            conn.commit()

    def list_jobs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        job_type: str | None = None,
        project_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        if job_type:
            clauses.append("job_type = %s")
            params.append(job_type)
        if project_ids is not None:
            if not project_ids:
                return []
            placeholders = ", ".join(["%s::uuid"] * len(project_ids))
            clauses.append(f"project_id IN ({placeholders})")
            params.extend(project_ids)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        query = f"""
            SELECT id, job_type, status, result, meta, project_id, created_by,
                   created_at, updated_at
            FROM jobs
            {where}
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            meta = row.get("meta") or {}
            if isinstance(meta, str):
                meta = json.loads(meta)
            result = row.get("result")
            if isinstance(result, str):
                result = json.loads(result)
            item = {
                "job_id": str(row["id"]),
                "job_type": row["job_type"],
                "status": row["status"],
                "project_id": (
                    str(row["project_id"])
                    if row.get("project_id") is not None
                    else None
                ),
                "created_by": (
                    str(row["created_by"])
                    if row.get("created_by") is not None
                    else None
                ),
                "created_at": (
                    row["created_at"].isoformat() if row["created_at"] else None
                ),
                "updated_at": (
                    row["updated_at"].isoformat() if row["updated_at"] else None
                ),
                **meta,
            }
            if result is not None:
                item["result"] = result
            items.append(item)
        return items

    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT status, meta, created_at
                FROM job_events
                WHERE job_id = %s::uuid
                ORDER BY created_at ASC
                """,
                (job_id,),
            ).fetchall()
        events = []
        for row in rows:
            meta = row.get("meta") or {}
            if isinstance(meta, str):
                meta = json.loads(meta)
            events.append(
                {
                    "status": row["status"],
                    "meta": meta,
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                }
            )
        return events
