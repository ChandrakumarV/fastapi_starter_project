from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_platform_access
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.user import UserInDB, UserResponse, UserUpdate
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(dependencies=[Depends(require_platform_access)], tags=["Profile"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get admin profile",
    description="Returns the profile of the authenticated admin user.",
)
async def get_admin_profile(
    current_admin: Annotated[UserInDB, Depends(require_platform_access)],
) -> UserResponse:
    return UserResponse.model_validate(current_admin)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update admin profile",
    description="Updates profile details (full_name, email, password) for the current admin.",
)
async def update_admin_profile(
    update_data: UserUpdate,
    current_admin: Annotated[UserInDB, Depends(require_platform_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
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
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete admin account",
    description="Soft deletes the current admin's account and clears session cookie.",
)
async def delete_admin_profile(
    response: Response,
    current_admin: Annotated[UserInDB, Depends(require_platform_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    success = await user_service.delete_user(db, current_admin.id)
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
