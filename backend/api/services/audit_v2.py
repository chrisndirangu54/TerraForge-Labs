from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def build_audit_event(payload: dict[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(payload, sort_keys=True)
    event_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": event_hash,
        "action": payload.get("action", "unknown"),
        "resource_type": payload.get("resource_type", "unknown"),
        "resource_id": payload.get("resource_id"),
        "actor": payload.get("actor", "system"),
        "metadata": payload.get("metadata", {}),
    }


class MemoryAuditStore:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = build_audit_event(payload)
        self._events.append(event)
        return event

    def list_events(
        self,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        events = self._events
        if resource_type:
            events = [
                event for event in events if event["resource_type"] == resource_type
            ]
        if resource_id:
            events = [
                event for event in events if event.get("resource_id") == resource_id
            ]
        return list(reversed(events[-limit:]))

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        for event in reversed(self._events):
            if event["event_id"] == event_id:
                return event
        return None

    def reset(self) -> None:
        self._events.clear()


_STORE: MemoryAuditStore | None = None


def get_audit_store() -> MemoryAuditStore:
    global _STORE
    if _STORE is None or os.getenv("AUDIT_STORE_BACKEND", "memory") == "memory":
        if _STORE is None:
            _STORE = MemoryAuditStore()
    return _STORE


def reset_audit_store() -> None:
    global _STORE
    _STORE = None
