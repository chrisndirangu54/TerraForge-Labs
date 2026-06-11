from __future__ import annotations

import os
import re
from typing import Any

_KNOWLEDGE_BASE = [
    {
        "id": "jorc-2012-sampling",
        "title": "JORC 2012 sampling techniques",
        "text": "Sampling techniques must document method, recovery, sub-sampling, and QA/QC controls.",
        "source": "docs/geology_primer.md",
    },
    {
        "id": "geobotany-indicators",
        "title": "Geobotanical indicator species",
        "text": "Metallophyte indicator species can highlight Cu-Co-Ni halos but require soil geochemistry confirmation.",
        "source": "docs/phase4-track-q-geobotany.md",
    },
    {
        "id": "kriging-uncertainty",
        "title": "Kriging uncertainty",
        "text": "Kriging variance grids quantify local estimation uncertainty and should inform drill spacing.",
        "source": "shared/constants.py",
    },
]


def _retrieve_documents(query: str, limit: int = 3) -> list[dict[str, str]]:
    tokens = {token.lower() for token in re.findall(r"[a-zA-Z]{3,}", query)}
    scored: list[tuple[int, dict[str, str]]] = []
    for doc in _KNOWLEDGE_BASE:
        haystack = f"{doc['title']} {doc['text']} {doc['source']}".lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return _KNOWLEDGE_BASE[:limit]
    return [doc for _score, doc in scored[:limit]]


def _build_stub_answer(
    query: str, docs: list[dict[str, str]], context: dict[str, Any]
) -> str:
    provider = os.getenv("LLM_PROVIDER", "stub")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    context_keys = ", ".join(sorted(context.keys()))
    citations = ", ".join(doc["id"] for doc in docs)
    return (
        f"[{provider}:{model}] {query[:120]} "
        f"(context_keys={context_keys}; citations={citations})"
    )


def rag_query(query: str, data_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = data_context or {}
    docs = _retrieve_documents(query)
    citations = [
        {
            "id": doc["id"],
            "title": doc["title"],
            "source": doc["source"],
            "excerpt": doc["text"][:160],
        }
        for doc in docs
    ]
    answer = _build_stub_answer(query, docs, context)
    if not citations:
        raise ValueError(
            "RAG response rejected: citation enforcement requires at least one source"
        )

    return {
        "query": query,
        "answer": answer,
        "citations": citations,
        "citation_count": len(citations),
        "provider": os.getenv("LLM_PROVIDER", "stub"),
    }


def generate_section(prompt: str, data_context: dict) -> str:
    result = rag_query(prompt, data_context)
    citation_ids = ", ".join(item["id"] for item in result["citations"])
    return f"{result['answer']} [citations: {citation_ids}]"
