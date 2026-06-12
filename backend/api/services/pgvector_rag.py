from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from backend.api.services.embedding import embed_text, embedding_dimension

_STORE: "PgvectorRAGStore | None" = None
_PGVECTOR_AVAILABLE: bool | None = None


def _pgvector_enabled() -> bool:
    backend = os.getenv("RAG_BACKEND", "tfidf").lower()
    return backend in {"pgvector", "hybrid"}


def _check_pgvector_extension() -> bool:
    global _PGVECTOR_AVAILABLE
    if _PGVECTOR_AVAILABLE is not None:
        return _PGVECTOR_AVAILABLE
    if os.getenv("INGEST_STORE_BACKEND", "memory") == "memory":
        _PGVECTOR_AVAILABLE = False
        return False
    try:
        from backend.api.db import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector' LIMIT 1"
                )
                _PGVECTOR_AVAILABLE = cur.fetchone() is not None
    except Exception:
        _PGVECTOR_AVAILABLE = False
    return _PGVECTOR_AVAILABLE


class PgvectorRAGStore(ABC):
    @abstractmethod
    def upsert_documents(self, docs: list[dict[str, str]]) -> int:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        project_id: str | None = None,
    ) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError


class MemoryPgvectorRAGStore(PgvectorRAGStore):
    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []

    def upsert_documents(self, docs: list[dict[str, str]]) -> int:
        embedded = 0
        for doc in docs:
            embedding = embed_text(f"{doc.get('title', '')} {doc.get('text', '')}")
            record = {**doc, "embedding": embedding["vector"], "provider": embedding["provider"]}
            self._docs = [item for item in self._docs if item.get("id") != doc.get("id")]
            self._docs.append(record)
            embedded += 1
        return embedded

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        project_id: str | None = None,
    ) -> list[dict[str, str]]:
        if not self._docs:
            return []
        query_embedding = embed_text(query)["vector"]

        def cosine(a: list[float], b: list[float]) -> float:
            length = min(len(a), len(b))
            if length == 0:
                return 0.0
            dot = sum(a[i] * b[i] for i in range(length))
            norm_a = sum(a[i] * a[i] for i in range(length)) ** 0.5
            norm_b = sum(b[i] * b[i] for i in range(length)) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored: list[tuple[float, dict[str, str]]] = []
        for doc in self._docs:
            if project_id and doc.get("project_id") and doc["project_id"] != project_id:
                continue
            score = cosine(query_embedding, doc.get("embedding", []))
            scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "source": doc["source"],
                "project_id": doc.get("project_id", ""),
            }
            for _score, doc in scored[:limit]
            if _score > 0
        ] or [
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "source": doc["source"],
                "project_id": doc.get("project_id", ""),
            }
            for doc in self._docs[:limit]
        ]

    def count(self) -> int:
        return len(self._docs)

    def reset(self) -> None:
        self._docs.clear()


class PostgresPgvectorRAGStore(PgvectorRAGStore):
    def upsert_documents(self, docs: list[dict[str, str]]) -> int:
        from backend.api.db import get_connection

        embedded = 0
        with get_connection() as conn:
            for doc in docs:
                embedding = embed_text(f"{doc.get('title', '')} {doc.get('text', '')}")
                vector = embedding["vector"]
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO rag_documents (
                            doc_id, project_id, title, text, source, embedding, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s::vector, %s::jsonb)
                        ON CONFLICT (doc_id) DO UPDATE SET
                            project_id = EXCLUDED.project_id,
                            title = EXCLUDED.title,
                            text = EXCLUDED.text,
                            source = EXCLUDED.source,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                        """,
                        (
                            doc["id"],
                            doc.get("project_id") or None,
                            doc.get("title", ""),
                            doc.get("text", ""),
                            doc.get("source", ""),
                            json.dumps(vector),
                            json.dumps({"embedding_provider": embedding["provider"]}),
                        ),
                    )
                embedded += 1
        return embedded

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        project_id: str | None = None,
    ) -> list[dict[str, str]]:
        from backend.api.db import get_connection

        query_embedding = embed_text(query)["vector"]
        clauses = ["TRUE"]
        params: list[Any] = [json.dumps(query_embedding), limit]
        if project_id:
            clauses.append("(project_id IS NULL OR project_id = %s)")
            params.insert(1, project_id)
        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT doc_id, title, text, source, project_id,
                   1 - (embedding <=> %s::vector) AS score
            FROM rag_documents
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = [json.dumps(query_embedding), *params[1:-1], json.dumps(query_embedding), limit]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "text": row[2],
                "source": row[3],
                "project_id": row[4] or "",
            }
            for row in rows
        ]

    def count(self) -> int:
        from backend.api.db import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM rag_documents")
                row = cur.fetchone()
        return int(row[0]) if row else 0

    def reset(self) -> None:
        from backend.api.db import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE rag_documents")


def get_pgvector_store() -> PgvectorRAGStore:
    global _STORE
    if _STORE is None:
        if _pgvector_enabled() and _check_pgvector_extension():
            _STORE = PostgresPgvectorRAGStore()
        else:
            _STORE = MemoryPgvectorRAGStore()
    return _STORE


def reset_pgvector_store() -> None:
    global _STORE, _PGVECTOR_AVAILABLE
    _STORE = None
    _PGVECTOR_AVAILABLE = None


def pgvector_status() -> dict[str, Any]:
    store = get_pgvector_store()
    return {
        "backend": os.getenv("RAG_BACKEND", "tfidf"),
        "store": "postgres" if isinstance(store, PostgresPgvectorRAGStore) else "memory",
        "pgvector_extension": _check_pgvector_extension(),
        "embedding_dim": embedding_dimension(),
        "documents": store.count(),
    }