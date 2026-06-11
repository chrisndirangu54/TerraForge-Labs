from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.dependencies import require_mutating_access
from backend.api.services.llm import rag_query

router = APIRouter()


@router.post("/copilot/query")
async def copilot_query(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    query = payload.get("query") or payload.get("question")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    context = {
        "project_id": payload.get("project_id"),
        "user_id": user.get("id"),
        **(payload.get("context") or {}),
    }
    return rag_query(str(query), context)


@router.post("/copilot/explain-anomaly")
async def explain_anomaly(
    payload: dict,
    user: dict = Depends(require_mutating_access),
) -> dict:
    anomaly_type = payload.get("anomaly_type", "geochemical")
    score = payload.get("score", payload.get("fusion_score", 0.0))
    query = f"Explain the {anomaly_type} anomaly with score {score} and recommend next field steps."
    return rag_query(
        query,
        {
            "project_id": payload.get("project_id"),
            "anomaly_type": anomaly_type,
            "score": score,
            "user_id": user.get("id"),
        },
    )
