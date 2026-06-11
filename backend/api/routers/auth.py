from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth.dependencies import get_current_user, validate_role
from backend.api.auth.jwt import create_access_token
from backend.api.auth.models import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.api.auth.repository import get_auth_repository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(payload: RegisterRequest) -> UserResponse:
    validate_role(payload.role)
    repo = get_auth_repository()
    try:
        user = repo.create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return UserResponse(**user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    repo = get_auth_repository()
    user = repo.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(
        user["id"], {"role": user["role"], "email": user["email"]}
    )
    return TokenResponse(access_token=token, user=UserResponse(**user))


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user.get("display_name"),
        role=user["role"],
    )
