from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.dependencies import require_platform
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.schemas.platform.tenant import (
    TenantCreate,
    TenantResponse,
    TenantStatusPatch,
    TenantUpdate,
)
from fastapi_starter_project.schemas.platform.user import UserInDB
from fastapi_starter_project.services.platform.tenant_service import tenant_service
from fastapi_starter_project.services.platform.user_service import user_service

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants Management"],
    dependencies=[Depends(require_platform)],
)


@router.get(
    "",
    response_model=list[TenantResponse],
    summary="List tenants",
    description="Returns a paginated list of tenants filtered by deleted status.",
)
async def list_tenants(
    db: Annotated[AsyncSession, Depends(get_db)],
    deleted: Annotated[bool, Query(description="Filter by deleted status")] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[TenantResponse]:
    tenants = await tenant_service.list_tenants(
        db, skip=skip, limit=limit, deleted=deleted
    )
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant details",
    description="Fetches detailed information for a specific tenant by ID, including soft-deleted tenants.",
)
async def get_tenant_details(
    tenant_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantResponse:
    tenant = await tenant_service.get_tenant_by_id(
        db, tenant_id, include_deleted=True
    )
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )
    return TenantResponse.model_validate(tenant)


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant and admin",
    description="Creates a new tenant and provisions its initial tenant administrator in a single database transaction.",
)
async def create_tenant(
    data: TenantCreate,
    current_admin: Annotated[UserInDB, Depends(require_platform)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantResponse:
    # 1. Validate username uniqueness
    if await user_service.get_by_username(db, data.user_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{data.user_name}' is already taken.",
        )

    # 2. Validate user email uniqueness
    if await user_service.get_by_email(db, str(data.user_email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{data.user_email}' is already registered.",
        )

    # 3. Create tenant + first admin atomically
    tenant, _ = await tenant_service.create_tenant_with_admin(
        db=db, data=data, creator_id=current_admin.id
    )
    return TenantResponse.model_validate(tenant)


@router.put(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant details",
    description="Updates existing tenant contact information and metadata.",
)
async def update_tenant(
    tenant_id: uuid.UUID,
    data: TenantUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantResponse:
    tenant = await tenant_service.update_tenant(db, tenant_id, data)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )
    return TenantResponse.model_validate(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant status or verification",
    description="Updates tenant active status or verification. Deactivating a tenant automatically revokes all its users' active sessions.",
)
async def patch_tenant_status(
    tenant_id: uuid.UUID,
    data: TenantStatusPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantResponse:
    tenant = await tenant_service.patch_tenant_status(db, tenant_id, data)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )
    return TenantResponse.model_validate(tenant)


@router.delete(
    "/{tenant_id}",
    response_model=MessageResponse,
    summary="Delete tenant",
    description="Soft deletes a tenant and invalidates all active sessions for users belonging to that tenant.",
)
async def delete_tenant(
    tenant_id: uuid.UUID,
    current_admin: Annotated[UserInDB, Depends(require_platform)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    deleted = await tenant_service.delete_tenant(
        db, tenant_id, deleted_by=current_admin.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found.",
        )
    return MessageResponse(message="Tenant deleted and all associated user sessions invalidated.")
