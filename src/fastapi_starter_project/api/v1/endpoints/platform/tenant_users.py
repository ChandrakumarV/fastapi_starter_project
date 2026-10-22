from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_tenant_access
from fastapi_starter_project.models.user import User
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.tenant_user import (
    TenantUserCreate,
    TenantUserPatch,
    TenantUserResponse,
    TenantUserUpdate,
    UserAuditBrief,
)
from fastapi_starter_project.schemas.user import UserInDB
from fastapi_starter_project.services.tenant_service import tenant_service
from fastapi_starter_project.services.user_service import user_service

router = APIRouter(
    prefix="/tenants/{tenant_id}/users",
    tags=["Tenant Users Management"],
    dependencies=[Depends(require_tenant_access)],
)


async def _serialize_user(db: AsyncSession, user: User) -> TenantUserResponse:
    created_by = None
    if user.created_by_id:
        stmt = select(User.name).where(User.id == user.created_by_id)
        c_name = (await db.execute(stmt)).scalar_one_or_none()
        created_by = UserAuditBrief(id=user.created_by_id, name=c_name or "Platform Admin")

    deleted_by = None
    if user.deleted_by_id:
        stmt = select(User.name).where(User.id == user.deleted_by_id)
        d_name = (await db.execute(stmt)).scalar_one_or_none()
        deleted_by = UserAuditBrief(id=user.deleted_by_id, name=d_name or "Platform Admin")

    return TenantUserResponse(
        id=user.id,
        created_at=user.created_at,
        created_by=created_by,
        name=user.name,
        user_name=user.user_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_deleted=user.is_deleted,
        deleted_at=user.deleted_at,
        deleted_by=deleted_by,
    )



@router.get(
    "",
    response_model=list[TenantUserResponse],
    summary="List tenant users",
    description="Returns all users belonging to a tenant. Use ?deleted_users=true to list soft-deleted users.",
)
async def list_tenant_users(
    tenant_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    deleted_users: Annotated[bool, Query(description="Filter deleted users")] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TenantUserResponse]:
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )
    users = await tenant_service.list_tenant_users(
        db, tenant_id, deleted_users=deleted_users, skip=skip, limit=limit
    )
    return [await _serialize_user(db, u) for u in users]


@router.get(
    "/{user_id}",
    response_model=TenantUserResponse,
    summary="Get tenant user details",
    description="Fetches detailed user information within a specific tenant.",
)
async def get_tenant_user_details(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantUserResponse:
    user = await tenant_service.get_tenant_user_by_id(db, tenant_id, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found in this tenant.",
        )
    return await _serialize_user(db, user)


@router.post(
    "",
    response_model=TenantUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant user",
    description="Provisions a new tenant user or tenant administrator within the specified tenant.",
)
async def create_tenant_user(
    tenant_id: uuid.UUID,
    data: TenantUserCreate,
    current_admin: Annotated[UserInDB, Depends(require_tenant_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantUserResponse:
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )

    if await user_service.get_by_username(db, data.user_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{data.user_name}' is already taken.",
        )

    if await user_service.get_by_email(db, str(data.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{data.email}' is already registered.",
        )

    user = await tenant_service.create_tenant_user(
        db, tenant_id, data, creator_id=current_admin.id
    )
    return await _serialize_user(db, user)


@router.put(
    "/{user_id}",
    response_model=TenantUserResponse,
    summary="Update tenant user details",
    description="Updates user profile fields and immediately revokes all active Redis sessions for that user.",
)
async def update_tenant_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TenantUserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantUserResponse:
    if data.user_name:
        existing = await user_service.get_by_username(db, data.user_name)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.user_name}' is already taken.",
            )

    if data.email:
        existing = await user_service.get_by_email(db, str(data.email))
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' is already registered.",
            )

    user = await tenant_service.update_tenant_user(db, tenant_id, user_id, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found in this tenant.",
        )
    return await _serialize_user(db, user)


@router.patch(
    "/{user_id}",
    response_model=TenantUserResponse,
    summary="Update user password or account status",
    description="Updates password or active/inactive status and immediately invalidates active sessions.",
)
async def patch_tenant_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TenantUserPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantUserResponse:
    user = await tenant_service.patch_tenant_user(db, tenant_id, user_id, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found in this tenant.",
        )
    return await _serialize_user(db, user)



@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete tenant user",
    description="Soft deletes a user from the tenant and revokes all active Redis sessions.",
)
async def delete_tenant_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    current_admin: Annotated[UserInDB, Depends(require_tenant_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account through this endpoint.",
        )

    deleted = await tenant_service.delete_tenant_user(
        db, tenant_id, user_id, deleter_id=current_admin.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found in this tenant.",
        )
    return MessageResponse(message="User deleted successfully and sessions revoked.")
