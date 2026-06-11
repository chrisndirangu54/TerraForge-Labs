from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.auth.dependencies import require_mutating_access


def mutating_router(**kwargs) -> APIRouter:
    """APIRouter that requires mutating access on every route."""
    return APIRouter(dependencies=[Depends(require_mutating_access)], **kwargs)
