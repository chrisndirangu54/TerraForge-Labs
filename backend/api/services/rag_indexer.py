from __future__ import annotations

from typing import Any


def index_completed_job(job_id: str, job_record: dict[str, Any]) -> dict[str, Any] | None:
    """Index a completed job result into the copilot RAG knowledge base."""

    status = job_record.get("status")
    if status != "complete":
        return None

    job_type = str(job_record.get("job_type", "unknown"))
    result = job_record.get("result") or {}
    project_id = None
    if isinstance(result, dict):
        project_id = result.get("project_id") or (result.get("payload") or {}).get(
            "project_id"
        )

    text_parts = [f"Job {job_id} type {job_type} completed."]
    if isinstance(result, dict):
        for key in ("summary", "metrics", "npv_usd", "label", "accuracy"):
            if key in result:
                text_parts.append(f"{key}: {result[key]}")
        if "metrics" in result and isinstance(result["metrics"], dict):
            for mk, mv in result["metrics"].items():
                text_parts.append(f"{mk}: {mv}")

    doc = {
        "id": f"job-{job_id}",
        "title": f"{job_type} job result",
        "text": " ".join(text_parts)[:2000],
        "source": f"jobs/{job_id}",
    }

    from backend.api.services.vector_rag import _get_index

    index = _get_index()
    index.add(doc)

    pgvector_count = 0
    import os

    if os.getenv("RAG_BACKEND", "tfidf").lower() in {"pgvector", "hybrid"}:
        try:
            from backend.api.services.pgvector_rag import get_pgvector_store

            pgvector_count = get_pgvector_store().upsert_documents([doc])
        except Exception:
            pgvector_count = 0

    return {
        "indexed": True,
        "job_id": job_id,
        "job_type": job_type,
        "project_id": project_id,
        "pgvector_documents": pgvector_count,
    }