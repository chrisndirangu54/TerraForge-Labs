from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

VALID_STATUSES = frozenset({"queued", "confirmed", "rejected"})


class MemoryLabelingStore:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def enqueue(self, payload: dict[str, Any]) -> dict[str, Any]:
        item_id = str(uuid4())
        item = {
            "id": item_id,
            "status": "queued",
            "species": payload.get("species", "unknown_vegetation"),
            "confidence": float(payload.get("confidence", 0.0)),
            "lon": float(payload.get("lon", 0.0)),
            "lat": float(payload.get("lat", 0.0)),
            "project_id": payload.get("project_id"),
            "image_upload_id": payload.get("image_upload_id"),
            "source": payload.get("source", "geobotany"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "confirmed_label": None,
        }
        self._items[item_id] = item
        return item

    def list_items(self, *, status: str | None = None) -> list[dict[str, Any]]:
        items = list(self._items.values())
        if status:
            items = [item for item in items if item["status"] == status]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items

    def get(self, item_id: str) -> dict[str, Any] | None:
        return self._items.get(item_id)

    def confirm(self, item_id: str, confirmed_label: str) -> dict[str, Any]:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Label queue item not found: {item_id}")
        item = {
            **item,
            "status": "confirmed",
            "confirmed_label": confirmed_label,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._items[item_id] = item
        return item

    def delete(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def reset(self) -> None:
        self._items.clear()


_STORE: MemoryLabelingStore | None = None


def get_labeling_store() -> MemoryLabelingStore:
    global _STORE
    if _STORE is None:
        _STORE = MemoryLabelingStore()
    return _STORE


def reset_labeling_store() -> None:
    global _STORE
    _STORE = None
