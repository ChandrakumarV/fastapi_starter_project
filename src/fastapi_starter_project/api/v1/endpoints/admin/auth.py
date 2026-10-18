from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.security import create_access_token, verify_password
from fastapi_starter_project.schemas.auth import LoginRequest, UsernameAvailabilityResponse
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["Admin Auth"])


@router.get(
    "/check-username",
    response_model=UsernameAvailabilityResponse,
    summary="Check username availability (Admin)",
    description="Real-time check to verify whether a username is available before creating an admin or user account.",
)
async def check_admin_username_availability(
    username: Annotated[
        str,
        Query(
            min_length=3,
            max_length=50,
            description="The username to check availability for",
            examples=["newadmin"],
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsernameAvailabilityResponse:
    existing_user = await user_service.get_by_username(db, username)
    if existing_user and not existing_user.is_deleted:
        return UsernameAvailabilityResponse(
            username=username,
            available=False,
            message=f"Username '{username}' is already taken.",
        )

    return UsernameAvailabilityResponse(
        username=username,
        available=True,
        message=f"Username '{username}' is available.",
    )


@router.post(
    "/login",
    response_model=MessageResponse,
    summary="Admin login",
    description="Authenticates admin credentials and sets an HTTP-only JWT cookie.",
)
async def admin_login(
    credentials: LoginRequest,
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
    if role_value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this endpoint.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin account. Please contact system support.",
        )

    token = create_access_token(subject=user.username, role=user.role)

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
    description="Clears the HTTP-only JWT authentication cookie for admin session.",
)
def admin_logout(response: Response) -> MessageResponse:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="Admin logged out successfully.")
