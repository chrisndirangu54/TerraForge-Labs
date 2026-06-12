from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _lineage_store() -> Path:
    path = _repo_root() / "artifacts" / "lineage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def content_hash(payload: dict[str, Any] | str | bytes) -> str:
    if isinstance(payload, bytes):
        material = payload
    elif isinstance(payload, str):
        material = payload.encode("utf-8")
    else:
        material = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def record_lineage(
    *,
    artifact_type: str,
    storage_key: str,
    job_id: str | None = None,
    project_id: str | None = None,
    model_version: str | None = None,
    dataset_hash: str | None = None,
    parent_hashes: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "id": str(uuid4()),
        "artifact_type": artifact_type,
        "storage_key": storage_key,
        "job_id": job_id,
        "project_id": project_id,
        "model_version": model_version,
        "dataset_hash": dataset_hash,
        "parent_hashes": parent_hashes or [],
        "metadata": metadata or {},
        "content_hash": content_hash({"storage_key": storage_key, "job_id": job_id}),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    store = _lineage_store()
    path = store / f"{record['id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def list_lineage(*, project_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    store = _lineage_store()
    records: list[dict[str, Any]] = []
    for path in store.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if project_id and record.get("project_id") != project_id:
            continue
        records.append(record)
    records.sort(key=lambda row: row.get("recorded_at", ""), reverse=True)
    return records[:limit]


def anchor_hash_on_chain(record_id: str) -> dict[str, Any]:
    """Content-addressed anchor stub — hash recorded for immutability audit."""

    store = _lineage_store()
    matches = list(store.glob("*.json"))
    record = None
    for path in matches:
        candidate = json.loads(path.read_text(encoding="utf-8"))
        if candidate.get("id") == record_id:
            record = candidate
            break
    if record is None:
        raise FileNotFoundError(f"Lineage record not found: {record_id}")

    anchor = content_hash(record)
    anchored = {
        **record,
        "blockchain_anchor": {
            "chain": "hash_anchor_stub",
            "tx_hash": anchor[:64],
            "anchored_at": datetime.now(timezone.utc).isoformat(),
            "method": "sha256_content_address",
        },
    }
    path = store / f"{record_id}.json"
    path.write_text(json.dumps(anchored, indent=2), encoding="utf-8")
    return anchored