from typing import Annotated
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
import jwt
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.services.session_service import session_service
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(tags=["Auth"])


class AdminLoginInput(BaseModel):
    username: str = Field(..., min_length=1, examples=["admin"])
    password: str = Field(..., min_length=4, examples=["password"])


@router.post(
    "/login",
    response_model=MessageResponse,
    summary="Admin login",
    description="Authenticates platform admin credentials with username and password, setting an HTTP-only JWT cookie.",
)
async def admin_login(
    credentials: AdminLoginInput,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    user = await user_service.get_by_username(db, credentials.username)
    if user and user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    allowed_roles = (
        UserRole.PLATFORM_ADMIN.value,
        UserRole.PLATFORM_USER.value,
    )
    if role_value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform privileges required to access this endpoint.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin account. Please contact system support.",
        )

    # Cache user profile directly in Redis session for sub-millisecond authentication.
    # Platform users never belong to any tenant (tenant_id is always None) and are tracked
    # purely by session_id and user_id in Redis.
    session_id = await session_service.create_session(
        user_id=user.id,
        tenant_id=None,
        role=role_value,
        extra_data={
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "created_by_id": str(user.created_by_id) if user.created_by_id else None,
            "is_active": user.is_active,
        },
    )

    token = create_access_token(
        subject=user.username,
        role=user.role,
        tenant_id=None,
        session_id=session_id,
    )

    max_age_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    return MessageResponse(message="Admin login successful.")


@router.delete(
    "/logout",
    response_model=MessageResponse,
    summary="Admin logout",
    description="Clears the HTTP-only JWT authentication cookie and invalidates the session in Redis if present.",
)
async def admin_logout(
    response: Response,
    access_token: Annotated[str | None, Cookie(alias=settings.COOKIE_NAME)] = None,
) -> MessageResponse:
    if access_token:
        try:
            payload = decode_access_token(access_token)
            if payload.session_id:
                await session_service.invalidate_session(payload.session_id)
        except Exception:
            try:
                unverified = jwt.decode(
                    access_token,
                    options={"verify_signature": False, "verify_exp": False},
                )
                session_id = unverified.get("session_id")
                if session_id:
                    await session_service.invalidate_session(session_id)
            except Exception:
                pass

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="Admin logged out successfully.")
