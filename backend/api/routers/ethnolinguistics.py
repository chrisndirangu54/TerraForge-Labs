from __future__ import annotations

from fastapi import APIRouter

from backend.api.auth.router import mutating_router

from backend.processing.ethnolinguistics import (
    community_attribution_report,
    interpret_local_term,
    knowledge_layer,
    record_ethnolinguistic_term,
    toponym_analysis,
)

router = mutating_router()


@router.post("/ethnolinguistics/record-term")
async def ethnolinguistics_record_term(payload: dict) -> dict:
    return record_ethnolinguistic_term(payload)


@router.post("/ethnolinguistics/interpret-term")
async def ethnolinguistics_interpret_term(payload: dict) -> dict:
    return interpret_local_term(
        payload.get("term", ""), payload.get("language_code", "und")
    )


@router.post("/ethnolinguistics/toponym-analysis")
async def ethnolinguistics_toponym_analysis(payload: dict) -> dict:
    return toponym_analysis(payload.get("features", []))


@router.post("/ethnolinguistics/community-attribution")
async def ethnolinguistics_community_attribution(payload: dict) -> dict:
    return community_attribution_report(payload.get("records", []))


@router.post("/ethnolinguistics/knowledge-layer")
async def ethnolinguistics_knowledge_layer(payload: dict) -> dict:
    return knowledge_layer(
        payload.get("records", []), bool(payload.get("include_restricted", False))
    )
