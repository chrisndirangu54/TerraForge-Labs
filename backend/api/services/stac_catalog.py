from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

_CATALOG: "StacCatalog | None" = None


class StacCatalog(ABC):
    @abstractmethod
    def register_artifact(self, record: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def register_stac_item(
        self,
        *,
        item: dict[str, Any],
        artifact_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_stac_item(self, item_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_stac_items(
        self,
        *,
        collection: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError


class MemoryStacCatalog(StacCatalog):
    def __init__(self) -> None:
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._items: dict[str, dict[str, Any]] = {}

    def register_artifact(self, record: dict[str, Any]) -> dict[str, Any]:
        artifact_id = record.get("id") or str(uuid4())
        stored = {**record, "id": artifact_id}
        self._artifacts[artifact_id] = stored
        return stored

    def register_stac_item(
        self,
        *,
        item: dict[str, Any],
        artifact_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        item_id = item["id"]
        stored = {
            "id": str(uuid4()),
            "item_id": item_id,
            "collection": item.get("collection", "terraforge-rasters"),
            "bbox": item.get("bbox"),
            "geometry": item.get("geometry"),
            "properties": item.get("properties", {}),
            "assets": item.get("assets", {}),
            "artifact_id": artifact_id,
            "project_id": project_id,
            "stac_version": item.get("stac_version", "1.0.0"),
            "links": item.get("links", []),
        }
        self._items[item_id] = stored
        return stored

    def get_stac_item(self, item_id: str) -> dict[str, Any] | None:
        return self._items.get(item_id)

    def list_stac_items(
        self,
        *,
        collection: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        items = list(self._items.values())
        if collection:
            items = [item for item in items if item.get("collection") == collection]
        if project_id:
            items = [item for item in items if item.get("project_id") == project_id]
        return items[:limit]

    def reset(self) -> None:
        self._artifacts.clear()
        self._items.clear()


class PostgresStacCatalog(StacCatalog):
    def register_artifact(self, record: dict[str, Any]) -> dict[str, Any]:
        from backend.api.db import get_connection

        artifact_id = record.get("id") or str(uuid4())
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    id, project_id, artifact_type, storage_key, content_type,
                    size_bytes, checksum, metadata
                )
                VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    metadata = EXCLUDED.metadata,
                    size_bytes = EXCLUDED.size_bytes
                """,
                (
                    artifact_id,
                    record.get("project_id"),
                    record.get("artifact_type", "raster"),
                    record["storage_key"],
                    record.get("content_type", "application/octet-stream"),
                    record.get("size_bytes", 0),
                    record.get("checksum"),
                    json.dumps(record.get("metadata") or {}),
                ),
            )
            conn.commit()
        return {**record, "id": artifact_id}

    def register_stac_item(
        self,
        *,
        item: dict[str, Any],
        artifact_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        from backend.api.db import get_connection

        row_id = str(uuid4())
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO stac_items (
                    id, collection, item_id, bbox, geometry, properties, assets,
                    artifact_id
                )
                VALUES (%s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::uuid)
                ON CONFLICT (item_id) DO UPDATE SET
                    properties = EXCLUDED.properties,
                    assets = EXCLUDED.assets,
                    artifact_id = EXCLUDED.artifact_id
                RETURNING id
                """,
                (
                    row_id,
                    item.get("collection", "terraforge-rasters"),
                    item["id"],
                    item.get("bbox"),
                    json.dumps(item.get("geometry") or {}),
                    json.dumps(item.get("properties") or {}),
                    json.dumps(item.get("assets") or {}),
                    artifact_id,
                ),
            )
            conn.commit()
        return {
            "id": row_id,
            "item_id": item["id"],
            "collection": item.get("collection"),
            "artifact_id": artifact_id,
            "project_id": project_id,
        }

    def get_stac_item(self, item_id: str) -> dict[str, Any] | None:
        from backend.api.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, collection, item_id, bbox, geometry, properties, assets,
                       artifact_id, created_at
                FROM stac_items WHERE item_id = %s
                """,
                (item_id,),
            ).fetchone()
        return _row_to_item(row) if row else None

    def list_stac_items(
        self,
        *,
        collection: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        from backend.api.db import get_connection

        clauses = []
        params: list[Any] = []
        if collection:
            clauses.append("collection = %s")
            params.append(collection)
        if project_id:
            clauses.append(
                "artifact_id IN (SELECT id FROM artifacts WHERE project_id = %s::uuid)"
            )
            params.append(project_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        query = f"""
            SELECT id, collection, item_id, bbox, geometry, properties, assets,
                   artifact_id, created_at
            FROM stac_items
            {where}
            ORDER BY created_at DESC
            LIMIT %s
        """
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_item(row) for row in rows]

    def reset(self) -> None:
        from backend.api.db import get_connection

        with get_connection() as conn:
            conn.execute("DELETE FROM stac_items")
            conn.execute("DELETE FROM artifacts")
            conn.commit()


def _row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    geometry = row.get("geometry") or {}
    properties = row.get("properties") or {}
    assets = row.get("assets") or {}
    if isinstance(geometry, str):
        geometry = json.loads(geometry)
    if isinstance(properties, str):
        properties = json.loads(properties)
    if isinstance(assets, str):
        assets = json.loads(assets)
    return {
        "id": str(row["id"]),
        "item_id": row["item_id"],
        "collection": row["collection"],
        "bbox": row.get("bbox"),
        "geometry": geometry,
        "properties": properties,
        "assets": assets,
        "artifact_id": str(row["artifact_id"]) if row.get("artifact_id") else None,
        "created_at": (
            row["created_at"].isoformat() if row.get("created_at") else None
        ),
        "stac_version": "1.0.0",
        "type": "Feature",
    }


def _backend_name() -> str:
    configured = os.getenv("STAC_CATALOG_BACKEND", "").lower()
    if configured:
        return configured
    from backend.api.db import db_available

    return "postgres" if db_available() else "memory"


def get_stac_catalog() -> StacCatalog:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG

    backend = _backend_name()
    if backend == "postgres":
        _CATALOG = PostgresStacCatalog()
    else:
        _CATALOG = MemoryStacCatalog()
    return _CATALOG


def reset_stac_catalog() -> None:
    global _CATALOG
    if _CATALOG is not None:
        _CATALOG.reset()
    _CATALOG = None
