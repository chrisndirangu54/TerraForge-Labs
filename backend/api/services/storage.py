from __future__ import annotations

import hashlib
import io
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4


class ObjectStorage(ABC):
    @property
    @abstractmethod
    def backend(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def put(
        self,
        key: str,
        content: bytes | str,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_signed_url(self, key: str, *, expires_seconds: int = 3600) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_keys(self, prefix: str = "") -> list[str]:
        raise NotImplementedError

    def reset(self) -> None:
        return None


class MemoryObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        self._objects: dict[str, dict[str, Any]] = {}

    @property
    def backend(self) -> str:
        return "memory"

    def put(
        self,
        key: str,
        content: bytes | str,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        record = {
            "id": str(uuid4()),
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
        return None if stored is None else stored["content"]

    def exists(self, key: str) -> bool:
        return key in self._objects

    def get_signed_url(self, key: str, *, expires_seconds: int = 3600) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)
        token = hashlib.sha256(f"{key}:{expires_at.isoformat()}".encode()).hexdigest()[
            :16
        ]
        return (
            f"memory://terraforge/{key}?expires={int(expires_at.timestamp())}&sig={token}"
        )

    def get_public_url(self, key: str) -> str:
        bucket = os.getenv("MINIO_BUCKET", "terraforge")
        return f"minio://{bucket}/{key}"

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(key for key in self._objects if key.startswith(prefix))

    def reset(self) -> None:
        self._objects.clear()


class MinioObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        from minio import Minio

        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        if "://" in endpoint:
            parsed = urlparse(endpoint)
            endpoint = parsed.netloc or parsed.path
            secure = parsed.scheme == "https"

        self._bucket = os.getenv("MINIO_BUCKET", "terraforge")
        self._client = Minio(
            endpoint,
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=secure,
        )
        self._ensure_bucket()

    @property
    def backend(self) -> str:
        return "minio"

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def put(
        self,
        key: str,
        content: bytes | str,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(payload),
            length=len(payload),
            content_type=content_type,
        )
        return {
            "id": str(uuid4()),
            "key": key,
            "size_bytes": len(payload),
            "content_type": content_type,
            "metadata": metadata or {},
            "checksum": hashlib.sha256(payload).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backend": self.backend,
        }

    def get(self, key: str) -> bytes | None:
        try:
            response = self._client.get_object(self._bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception:
            return None

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except Exception:
            return False

    def get_signed_url(self, key: str, *, expires_seconds: int = 3600) -> str:
        return self._client.presigned_get_object(
            self._bucket,
            key,
            expires=timedelta(seconds=expires_seconds),
        )

    def get_public_url(self, key: str) -> str:
        return f"minio://{self._bucket}/{key}"

    def list_keys(self, prefix: str = "") -> list[str]:
        keys: list[str] = []
        for obj in self._client.list_objects(self._bucket, prefix=prefix, recursive=True):
            keys.append(obj.object_name)
        return sorted(keys)


# Backwards-compatible alias used across the codebase.
StorageService = ObjectStorage

_SERVICE: ObjectStorage | None = None


def get_storage_service() -> ObjectStorage:
    global _SERVICE
    if _SERVICE is not None:
        return _SERVICE

    backend = os.getenv("STORAGE_BACKEND", "memory").lower()
    if backend == "minio":
        _SERVICE = MinioObjectStorage()
    else:
        _SERVICE = MemoryObjectStorage()
    return _SERVICE


def reset_storage_service() -> None:
    global _SERVICE
    if _SERVICE is not None:
        _SERVICE.reset()
    _SERVICE = None