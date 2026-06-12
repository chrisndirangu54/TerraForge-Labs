from __future__ import annotations

import os
import re
from typing import Any

_KNOWLEDGE_BASE = [
    {
        "id": "jorc-2012-sampling",
        "title": "JORC 2012 sampling techniques",
        "text": (
            "Sampling techniques must document method, recovery, sub-sampling, "
            "and QA/QC controls with chain-of-custody."
        ),
        "source": "docs/geology_primer.md",
    },
    {
        "id": "geobotany-indicators",
        "title": "Geobotanical indicator species",
        "text": (
            "Metallophyte indicator species can highlight Cu-Co-Ni halos but "
            "require soil geochemistry confirmation and seasonal controls."
        ),
        "source": "docs/phase4-track-q-geobotany.md",
    },
    {
        "id": "kriging-uncertainty",
        "title": "Kriging uncertainty",
        "text": (
            "Kriging variance grids quantify local estimation uncertainty and "
            "should inform drill spacing and infill programs."
        ),
        "source": "shared/constants.py",
    },
    {
        "id": "instrument-ingest",
        "title": "Instrument ingest provenance",
        "text": (
            "Every observation requires project_id, source, parser_version, and "
            "CRS for auditable geoscience workflows."
        ),
        "source": "docs/schemas/instrument_readings.md",
    },
    {
        "id": "security-baseline",
        "title": "Security and project isolation",
        "text": (
            "Authenticated users only access project memberships; mutating "
            "routes require JWT when AUTH_REQUIRED=true."
        ),
        "source": "docs/security-baseline.md",
    },
    {
        "id": "fusion-targeting",
        "title": "Multimodal fusion targeting",
        "text": (
            "Fusion scores combine geochemistry, geobotany, spectral, and "
            "structural layers with per-factor contribution breakdown."
        ),
        "source": "backend/processing/fusion_engine.py",
    },
]


def _provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "stub").lower()


def _use_gemini() -> bool:
    if os.getenv("LLM_FORCE_STUB", "").lower() in {"1", "true", "yes"}:
        return False
    if _provider_name() != "gemini":
        return False
    from backend.api.services.gemini_client import is_gemini_configured

    return is_gemini_configured()


def _retrieve_documents(
    query: str,
    limit: int = 3,
    *,
    project_id: str | None = None,
) -> list[dict[str, str]]:
    from backend.api.services.vector_rag import vector_search

    hits = vector_search(query, limit=limit, project_id=project_id)
    if hits:
        return hits
    return _KNOWLEDGE_BASE[:limit]


def _format_citation_block(citations: list[dict[str, str]]) -> str:
    lines = ["Sources:"]
    for item in citations:
        lines.append(f"- [{item['id']}] {item['title']} ({item['source']})")
    return "\n".join(lines)


def _build_stub_answer(
    query: str, docs: list[dict[str, str]], context: dict[str, Any]
) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    context_keys = ", ".join(sorted(context.keys())) or "none"
    citations = ", ".join(doc["id"] for doc in docs)
    return (
        f"[stub:{model}] {query[:200]} "
        f"(context={context_keys}; citations={citations})"
    )


def _build_gemini_answer(
    query: str,
    docs: list[dict[str, str]],
    context: dict[str, Any],
) -> dict[str, Any]:
    from backend.api.services.gemini_client import generate_text

    context_lines = [
        f"{key}: {value}" for key, value in sorted(context.items()) if value
    ]
    source_lines = [
        f"[{doc['id']}] {doc['title']}: {doc['text']} (source: {doc['source']})"
        for doc in docs
    ]
    system_instruction = (
        "You are TerraForge Geo Copilot, a geoscience assistant. "
        "Answer using ONLY the provided sources and project context. "
        "If evidence is insufficient, say what data is missing. "
        "End with a 'Sources:' section listing citation ids in brackets."
    )
    prompt = (
        f"Question: {query}\n\n"
        f"Project context:\n"
        + ("\n".join(context_lines) if context_lines else "none")
        + "\n\nRetrieved sources:\n"
        + "\n".join(source_lines)
    )
    result = generate_text(prompt, system_instruction=system_instruction)
    answer = result["text"]
    if "Sources:" not in answer:
        answer = f"{answer}\n\n{_format_citation_block(docs)}"
    return {
        "answer": answer,
        "provider": result["provider"],
        "model": result["model"],
        "prompt_tokens": result.get("prompt_tokens"),
        "output_tokens": result.get("output_tokens"),
    }


def rag_query(query: str, data_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = data_context or {}
    docs = _retrieve_documents(
        query,
        project_id=context.get("project_id"),
    )
    citations = [
        {
            "id": doc["id"],
            "title": doc["title"],
            "source": doc["source"],
            "excerpt": doc["text"][:160],
        }
        for doc in docs
    ]
    if not citations:
        raise ValueError(
            "RAG response rejected: citation enforcement requires at least one source"
        )

    if _use_gemini():
        try:
            generated = _build_gemini_answer(query, docs, context)
            answer = generated["answer"]
            provider = generated["provider"]
            model = generated["model"]
            meta = {
                "prompt_tokens": generated.get("prompt_tokens"),
                "output_tokens": generated.get("output_tokens"),
                "retrieval": "vector_tfidf",
                "retrieved_ids": [doc["id"] for doc in docs],
            }
        except Exception as exc:
            answer = (
                f"{_build_stub_answer(query, docs, context)} "
                f"[gemini_fallback: {exc}]"
            )
            provider = "stub"
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            meta = {
                "gemini_error": str(exc),
                "retrieval": "vector_tfidf",
                "retrieved_ids": [doc["id"] for doc in docs],
            }
    else:
        answer = _build_stub_answer(query, docs, context)
        provider = "stub"
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        meta = {
            "retrieval": "vector_tfidf",
            "retrieved_ids": [doc["id"] for doc in docs],
        }

    return {
        "query": query,
        "answer": answer,
        "citations": citations,
        "citation_count": len(citations),
        "provider": provider,
        "model": model,
        "meta": meta,
    }


def generate_section(prompt: str, data_context: dict) -> str:
    result = rag_query(prompt, data_context)
    citation_ids = ", ".join(item["id"] for item in result["citations"])
    return f"{result['answer']}\n\n[citations: {citation_ids}]"


def llm_status() -> dict[str, Any]:
    from backend.api.services.gemini_client import is_gemini_configured

    return {
        "provider": _provider_name(),
        "gemini_configured": is_gemini_configured(),
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "active": _use_gemini(),
    }