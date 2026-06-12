import os

from backend.api.services.embedding import embed_text
from backend.api.services.pgvector_rag import (
    MemoryPgvectorRAGStore,
    reset_pgvector_store,
)
from backend.api.services.vector_rag import rebuild_vector_index, reset_vector_index, vector_search


def setup_function() -> None:
    os.environ["RAG_BACKEND"] = "hybrid"
    reset_vector_index()
    reset_pgvector_store()


def test_hash_embedding_is_normalized():
    result = embed_text("JORC sampling QA/QC controls")
    assert result["provider"] == "hash"
    assert len(result["vector"]) == 768


def test_pgvector_memory_store_search():
    store = MemoryPgvectorRAGStore()
    store.upsert_documents(
        [
            {
                "id": "ingest-1",
                "title": "Matuu Ta anomaly",
                "text": "ta_ppm elevated to 410 ppm near sample MTU-900",
                "source": "ingest/matuu",
                "project_id": "matuu",
            }
        ]
    )
    hits = store.search("ta_ppm matuu anomaly", project_id="matuu", limit=3)
    assert hits
    assert hits[0]["id"] == "ingest-1"


def test_hybrid_rebuild_indexes_pgvector_documents():
    stats = rebuild_vector_index(project_id=None)
    assert stats["indexed_documents"] >= 6
    assert stats["pgvector_documents"] >= 6
    hits = vector_search("kriging uncertainty drill spacing", limit=3)
    assert hits