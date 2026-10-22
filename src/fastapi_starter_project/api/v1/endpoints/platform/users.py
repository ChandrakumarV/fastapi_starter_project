import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_platform_admin
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.user import (
    UserCreateAdmin,
    UserInDB,
    UserResponse,
    UserStatusUpdate,
)
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(dependencies=[Depends(require_platform_admin)], tags=["Users"])

PLATFORM_ROLES = (
    UserRole.PLATFORM_ADMIN.value,
    UserRole.PLATFORM_USER.value,
)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create platform user",
    description="Allows platform administrators to create platform accounts (platform_admin or platform_user).",
)
async def create_user_by_admin(
    user_in: UserCreateAdmin,
    current_admin: Annotated[UserInDB, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    role_val = user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role)
    if role_val not in (UserRole.PLATFORM_ADMIN.value, UserRole.PLATFORM_USER.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform user management can only create platform roles ('platform_admin', 'platform_user').",
        )

    if await user_service.get_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' is already registered.",
        )
    if await user_service.get_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user_in.email}' is already registered.",
        )

    new_user = await user_service.create_user(
        db=db,
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        password=user_in.password,
        role=role_val,
        created_by_id=current_admin.id,
    )
    return UserResponse.model_validate(new_user)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List platform admin users",
    description="Returns a paginated list of platform admin users in the system.",
)
async def list_all_users(
    current_admin: Annotated[UserInDB, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
) -> list[UserResponse]:
    users = await user_service.list_users(
        db,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        roles=list(PLATFORM_ROLES),
    )
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get platform admin user details by ID",
    description="Allows administrators to view details of any platform admin user by ID.",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_admin: Annotated[UserInDB, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await user_service.get_by_id(db, user_id)
    if not user or user.role not in PLATFORM_ROLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform admin user with ID {user_id} not found.",
        )
    return UserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Update platform admin active/inactive status",
    description="Allows administrators to activate or deactivate a platform admin account.",
)
async def set_user_status(
    user_id: uuid.UUID,
    status_in: UserStatusUpdate,
    current_admin: Annotated[UserInDB, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    target_user = await user_service.get_by_id(db, user_id)
    if not target_user or target_user.role not in PLATFORM_ROLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform admin user with ID {user_id} not found or has been deleted.",
        )

    user = await user_service.set_user_active_status(db, user_id, status_in.is_active)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found or has been deleted.",
        )
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Soft delete a platform admin user",
    description="Soft deletes a platform admin user account. Never performs a physical row deletion.",
)
async def soft_delete_user_by_admin(
    user_id: uuid.UUID,
    current_admin: Annotated[UserInDB, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account through the user management endpoint. Use /platform/me instead.",
        )

    target_user = await user_service.get_by_id(db, user_id)
    if not target_user or target_user.role not in PLATFORM_ROLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform admin user with ID {user_id} not found or already deleted.",
        )

    success = await user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found or already deleted.",
        )
    return MessageResponse(message=f"Platform admin user {user_id} soft deleted successfully.")
