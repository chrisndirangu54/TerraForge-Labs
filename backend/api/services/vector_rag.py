from __future__ import annotations

import math
import re
from typing import Any

_STATIC_KNOWLEDGE_BASE = [
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

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]{3,}")
_INDEX: dict[str, Any] | None = None


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _document_text(doc: dict[str, str]) -> str:
    return f"{doc.get('title', '')} {doc.get('text', '')} {doc.get('source', '')}"


class _TfidfIndex:
    def __init__(self) -> None:
        self._docs: list[dict[str, str]] = []
        self._vectors: list[dict[str, float]] = []
        self._idf: dict[str, float] = {}

    def clear(self) -> None:
        self._docs.clear()
        self._vectors.clear()
        self._idf.clear()

    def add(self, doc: dict[str, str]) -> None:
        self._docs.append(doc)
        self._rebuild()

    def extend(self, docs: list[dict[str, str]]) -> None:
        self._docs.extend(docs)
        self._rebuild()

    def _rebuild(self) -> None:
        tokenized = [_tokenize(_document_text(doc)) for doc in self._docs]
        doc_count = max(1, len(tokenized))
        df: dict[str, int] = {}
        for tokens in tokenized:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        self._idf = {
            token: math.log((1 + doc_count) / (1 + count)) + 1.0
            for token, count in df.items()
        }
        self._vectors = [self._tfidf(tokens) for tokens in tokenized]

    def _tfidf(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = float(len(tokens))
        vector: dict[str, float] = {}
        for token, count in counts.items():
            tf = count / total
            vector[token] = tf * self._idf.get(token, 1.0)
        norm = math.sqrt(sum(weight * weight for weight in vector.values()))
        if norm > 0:
            vector = {token: weight / norm for token, weight in vector.items()}
        return vector

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        if len(a) > len(b):
            a, b = b, a
        return sum(weight * b.get(token, 0.0) for token, weight in a.items())

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        project_id: str | None = None,
    ) -> list[dict[str, str]]:
        if not self._docs:
            return []
        query_vec = self._tfidf(_tokenize(query))
        scored: list[tuple[float, dict[str, str]]] = []
        for doc, vector in zip(self._docs, self._vectors, strict=True):
            if project_id and doc.get("project_id") and doc["project_id"] != project_id:
                continue
            score = self._cosine(query_vec, vector)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored:
            return [doc for _score, doc in scored[:limit]]
        candidates = self._docs
        if project_id:
            scoped = [doc for doc in candidates if doc.get("project_id") == project_id]
            if scoped:
                candidates = scoped
        return candidates[:limit]


def _get_index() -> _TfidfIndex:
    global _INDEX
    if _INDEX is None:
        index = _TfidfIndex()
        index.extend(list(_STATIC_KNOWLEDGE_BASE))
        _INDEX = {"index": index, "last_project_id": None}
    return _INDEX["index"]


def reset_vector_index() -> None:
    global _INDEX
    _INDEX = None


def _observation_document(row: dict[str, Any]) -> dict[str, str]:
    data = row.get("data") or {}
    element_bits = [
        f"{key}={value}"
        for key, value in sorted(data.items())
        if isinstance(value, (int, float))
    ][:8]
    sample_id = row.get("sample_id") or row.get("id")
    lon = row.get("lon")
    lat = row.get("lat")
    text = (
        f"Ingest observation {sample_id} for project {row.get('project_id')} "
        f"from source {row.get('source')} via {row.get('parser_version')}. "
        f"Coordinates: lon={lon}, lat={lat}. "
        f"Instrument={row.get('instrument_type')}. "
        f"Values: {', '.join(element_bits) or 'no numeric payload'}."
    )
    if row.get("flagged"):
        text += f" Flagged: {', '.join(row.get('flag_reasons') or [])}."
    return {
        "id": f"ingest-{row.get('id', sample_id)}",
        "title": f"Ingest observation {sample_id}",
        "text": text,
        "source": f"ingest/{row.get('project_id')}",
        "project_id": str(row.get("project_id") or ""),
    }


def _report_documents(report: dict[str, Any]) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    project = str(report.get("project") or report.get("project_name") or "unknown")
    report_id = str(report.get("report_id"))
    sections = report.get("sections") or {}
    for section_name, section_body in sections.items():
        if isinstance(section_body, dict) and "text" in section_body:
            text = str(section_body.get("text", ""))
            docs.append(
                {
                    "id": f"report-{report_id}-{section_name}",
                    "title": f"JORC report {report_id} — {section_name}",
                    "text": text,
                    "source": f"reports/{report_id}",
                    "project_id": project,
                }
            )
            continue
        if not isinstance(section_body, dict):
            continue
        for criterion, payload in section_body.items():
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text", "")).strip()
            if not text:
                continue
            docs.append(
                {
                    "id": f"report-{report_id}-{section_name}-{criterion}",
                    "title": f"JORC {section_name}: {criterion}",
                    "text": text,
                    "source": f"reports/{report_id}",
                    "project_id": project,
                }
            )
    return docs


def rebuild_vector_index(*, project_id: str | None = None, limit: int = 200) -> dict[str, Any]:
    from backend.api.services.ingest import list_project_observations
    from backend.api.services.jorc_report import get_report_store

    index = _get_index()
    index.clear()
    index.extend(list(_STATIC_KNOWLEDGE_BASE))

    listed = list_project_observations(project_id=project_id, limit=limit)
    ingest_rows = listed.get("items") or listed.get("observations") or []
    ingest_docs = [_observation_document(row) for row in ingest_rows]
    report_docs: list[dict[str, str]] = []
    for report in get_report_store().list_reports():
        if project_id and str(report.get("project")) != project_id:
            continue
        report_docs.extend(_report_documents(report))

    index.extend(ingest_docs)
    index.extend(report_docs)

    global _INDEX
    if _INDEX is not None:
        _INDEX["last_project_id"] = project_id

    return {
        "indexed_documents": len(index._docs),
        "ingest_documents": len(ingest_docs),
        "report_documents": len(report_docs),
        "static_documents": len(_STATIC_KNOWLEDGE_BASE),
        "project_id": project_id,
    }


def ensure_index_for_project(project_id: str | None) -> None:
    global _INDEX
    if _INDEX is None:
        rebuild_vector_index(project_id=project_id)
        return
    if project_id and _INDEX.get("last_project_id") != project_id:
        rebuild_vector_index(project_id=project_id)


def vector_search(
    query: str,
    *,
    limit: int = 5,
    project_id: str | None = None,
) -> list[dict[str, str]]:
    ensure_index_for_project(project_id)
    return _get_index().search(query, limit=limit, project_id=project_id)


def vector_index_status() -> dict[str, Any]:
    index = _get_index()
    project_ids = sorted(
        {doc.get("project_id") for doc in index._docs if doc.get("project_id")}
    )
    sources = sorted({doc.get("source", "") for doc in index._docs if doc.get("source")})
    return {
        "retrieval": "tfidf_cosine",
        "indexed_documents": len(index._docs),
        "project_ids": project_ids,
        "source_prefixes": sources[:20],
        "last_project_id": _INDEX.get("last_project_id") if _INDEX else None,
    }