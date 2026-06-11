from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


class StorageService:
    """Memory-backed object storage with MinIO-style signed URL stubs."""

    def __init__(self, *, backend: str = "memory") -> None:
        self.backend = backend
        self._objects: dict[str, dict[str, Any]] = {}

    def put(
        self,
        key: str,
        content: bytes | str,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        object_id = str(uuid4())
        record = {
            "id": object_id,
            "key": key,
            "size_bytes": len(payload),
            "content_type": content_type,
            "metadata": metadata or {},
            "checksum": hashlib.sha256(payload).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backend": self.backend,
        }
        self._objects[key] = {"record": record, "content": payload}
        return record

    def get(self, key: str) -> bytes | None:
        stored = self._objects.get(key)
        if stored is None:
            return None
        return stored["content"]

    def exists(self, key: str) -> bool:
        return key in self._objects

    def get_signed_url(self, key: str, *, expires_seconds: int = 3600) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)
        token = hashlib.sha256(f"{key}:{expires_at.isoformat()}".encode()).hexdigest()[
            :16
        ]
        if self.backend == "minio":
            endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
            bucket = os.getenv("MINIO_BUCKET", "terraforge")
            return (
                f"{endpoint}/{bucket}/{key}"
                f"?X-Amz-Expires={expires_seconds}&X-Amz-Signature={token}"
            )
        return f"memory://terraforge/{key}?expires={int(expires_at.timestamp())}&sig={token}"

    def get_public_url(self, key: str) -> str:
        return f"minio://terraforge/{key}"

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(key for key in self._objects if key.startswith(prefix))

    def reset(self) -> None:
        self._objects.clear()


_SERVICE: StorageService | None = None


def get_storage_service() -> StorageService:
    global _SERVICE
    if _SERVICE is None:
        backend = os.getenv("STORAGE_BACKEND", "memory").lower()
        _SERVICE = StorageService(backend=backend)
    return _SERVICE


def reset_storage_service() -> None:
    global _SERVICE
    _SERVICE = None
