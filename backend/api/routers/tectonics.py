from __future__ import annotations


from backend.api.auth.router import mutating_router

from backend.processing.tectonic_context import infer_tectonic_context

router = mutating_router()


@router.post("/tectonic-context")
async def tectonic_context(payload: dict) -> dict:
    return infer_tectonic_context(payload.get("bbox", [37.45, -1.2, 37.55, -1.1]))
