from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.auth.jwt import decode_access_token
from backend.api.auth.repository import get_auth_repository
from backend.api.auth.settings import VALID_ROLES, is_auth_required

_bearer = HTTPBearer(auto_error=False)


def _resolve_user(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )
    user = get_auth_repository().get_user_by_id(str(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict | None:
    return _resolve_user(credentials.credentials if credentials else None)


async def get_current_user(
    user: Annotated[dict | None, Depends(get_optional_user)],
) -> dict:
    if user is None:
        if is_auth_required():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return {
            "id": "anonymous",
            "email": "anonymous@local",
            "display_name": "Anonymous",
            "role": "admin",
        }
    return user


def require_roles(*roles: str):
    async def _checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in roles and user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return _checker


def require_mutating_access(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    if is_auth_required() and user.get("id") == "anonymous":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if user["role"] == "regulator_readonly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read-only role cannot mutate resources",
        )
    return user


def validate_role(role: str) -> str:
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
        )
    return role
