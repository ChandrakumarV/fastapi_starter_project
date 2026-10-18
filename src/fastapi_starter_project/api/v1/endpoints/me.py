from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_user
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.user import UserInDB, UserResponse, UserUpdate
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(dependencies=[Depends(require_user)], tags=["Profile"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: Annotated[UserInDB, Depends(require_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Updates personal profile fields (full_name, email, password) for the authenticated user.",
)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: Annotated[UserInDB, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    if update_data.email and update_data.email != current_user.email:
        existing = await user_service.get_by_email(db, update_data.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already taken by another account.",
            )

    updated_user = await user_service.update_user(db, current_user.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete current user account",
    description="Deletes the authenticated user's account and clears session cookie.",
)
async def delete_current_user_account(
    response: Response,
    current_user: Annotated[UserInDB, Depends(require_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    success = await user_service.delete_user(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="User account deleted successfully.")
