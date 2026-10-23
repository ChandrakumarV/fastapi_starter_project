from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_platform
from fastapi_starter_project.core.security import verify_password
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.platform.user import (
    UserInDB,
    UserPasswordUpdate,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from fastapi_starter_project.services.platform.user_service import user_service

router = APIRouter(dependencies=[Depends(require_platform)], tags=["Profile"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get admin profile",
    description="Returns the profile of the authenticated admin user without soft-delete audit fields.",
)
async def get_admin_profile(
    current_admin: Annotated[UserInDB, Depends(require_platform)],
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_admin)


@router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="Update admin profile",
    description="Updates profile details (username, full_name, email, phone) for the current user.",
)
async def update_admin_profile(
    update_data: UserUpdate,
    current_admin: Annotated[UserInDB, Depends(require_platform)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileResponse:
    if update_data.username and update_data.username != current_admin.username:
        existing_username = await user_service.get_by_username(db, update_data.username)
        if existing_username and existing_username.id != current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{update_data.username}' is already taken.",
            )

    if update_data.email and update_data.email != current_admin.email:
        existing = await user_service.get_by_email(db, update_data.email)
        if existing and existing.id != current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already taken by another account.",
            )

    updated_user = await user_service.update_user(db, current_admin.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found.",
        )
    return UserProfileResponse.model_validate(updated_user)


@router.patch(
    "/me",
    response_model=MessageResponse,
    summary="Update current user password",
    description="Updates the password for the current authenticated user after verifying old password, and invalidates all active sessions.",
)
async def update_current_user_password(
    password_data: UserPasswordUpdate,
    current_admin: Annotated[UserInDB, Depends(require_platform)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    # 1. Fetch user to verify old password
    user = await user_service.get_by_id(db, current_admin.id)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not verify_password(password_data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password.",
        )

    # 2. Update password and invalidate active sessions in Redis
    await user_service.change_password(db, current_admin.id, password_data.new_password)

    return MessageResponse(message="Password updated successfully.")


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete admin account",
    description="Soft deletes the current admin's account and clears session cookie.",
)
async def delete_admin_profile(
    response: Response,
    current_admin: Annotated[UserInDB, Depends(require_platform)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    success = await user_service.delete_user(
        db, current_admin.id, deleted_by=current_admin.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found.",
        )

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="Admin account deleted successfully.")
