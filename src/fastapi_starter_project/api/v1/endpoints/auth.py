from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.security import create_access_token, verify_password
from fastapi_starter_project.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UsernameAvailabilityResponse,
)
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.user import UserResponse
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(tags=["Authentication"])


@router.get(
    "/auth/check-username",
    response_model=UsernameAvailabilityResponse,
    summary="Check username availability",
    description="Real-time check to verify whether a username is available during registration.",
)
async def check_username_availability(
    username: Annotated[
        str,
        Query(
            min_length=3,
            max_length=50,
            description="The username to check availability for",
            examples=["john_doe"],
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
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User self-registration",
    description="Public registration for normal users. Validates username and email availability.",
)
async def register(
    register_data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    # 1. Verify username availability
    if await user_service.get_by_username(db, register_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{register_data.username}' is already taken.",
        )

    # 2. Verify email availability
    if await user_service.get_by_email(db, register_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{register_data.email}' is already registered.",
        )

    # 3. Create user with default 'user' role
    new_user = await user_service.create_user(
        db=db,
        username=register_data.username,
        email=register_data.email,
        full_name=register_data.full_name,
        password=register_data.password,
        role="user",
    )
    return UserResponse.model_validate(new_user)


@router.post(
    "/auth/login",
    response_model=MessageResponse,
    summary="User login",
    description="Authenticates credentials and sets an HTTP-only JWT cookie.",
)
async def login(
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
    if role_value != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User privileges required to access this endpoint.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Please contact an administrator.",
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

    return MessageResponse(message="Login successful.")


@router.delete(
    "/auth/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Clears the HTTP-only JWT authentication cookie.",
)
def logout(response: Response) -> MessageResponse:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="Logged out successfully.")
