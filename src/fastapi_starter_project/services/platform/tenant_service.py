from datetime import datetime, timezone
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.security import get_password_hash
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.models.tenant import Tenant
from fastapi_starter_project.models.user import User
from fastapi_starter_project.schemas.platform.tenant import (
    TenantCreate,
    TenantStatusPatch,
    TenantUpdate,
)
from fastapi_starter_project.schemas.platform.tenant_user import (
    TenantUserCreate,
    TenantUserPatch,
    TenantUserUpdate,
)
from fastapi_starter_project.services.session_service import session_service


class TenantService:
    """Handles tenant provisioning, tenant lifecycle, and tenant user management."""

    # -------------------------------------------------------------
    # Tenant Operations
    # -------------------------------------------------------------
    async def create_tenant_with_admin(
        self, db: AsyncSession, data: TenantCreate, creator_id: uuid.UUID | None = None
    ) -> tuple[Tenant, User]:
        """
        Creates a tenant and its first tenant admin in a single atomic database transaction.
        """
        tenant = Tenant(
            id=uuid.uuid4(),
            name=data.name,
            phone_no=data.phone_no,
            email=str(data.email),
            address=data.address,
            district=data.district,
            pincode=data.pincode,
            is_verified=data.is_verified,
            is_active=data.is_active,
            is_deleted=False,
            created_by=creator_id,
        )
        db.add(tenant)
        await db.flush()

        tenant_admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            full_name=data.full_name,
            user_name=data.user_name,
            email=str(data.user_email),
            phone=data.user_phone,
            role=UserRole.TENANT_ADMIN.value,
            hashed_password=get_password_hash(data.password),
            is_active=True,
            is_deleted=False,
            created_by=creator_id,
        )
        db.add(tenant_admin)
        await db.commit()
        await db.refresh(tenant)
        await db.refresh(tenant_admin)

        return tenant, tenant_admin

    async def get_tenant_by_id(
        self, db: AsyncSession, tenant_id: uuid.UUID, include_deleted: bool = False
    ) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        if not include_deleted:
            stmt = stmt.where(Tenant.is_deleted == False)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_tenant_by_name_or_email(
        self, db: AsyncSession, name: str, email: str
    ) -> Tenant | None:
        stmt = select(Tenant).where(
            or_(Tenant.name == name, Tenant.email == email),
            Tenant.is_deleted == False,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def list_tenants(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[Tenant]:
        stmt = (
            select(Tenant)
            .where(Tenant.is_deleted == deleted)
            .order_by(Tenant.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list((await db.execute(stmt)).scalars().all())

    async def update_tenant(
        self, db: AsyncSession, tenant_id: uuid.UUID, data: TenantUpdate
    ) -> Tenant | None:
        tenant = await self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None

        if data.name is not None:
            tenant.name = data.name
        if data.phone_no is not None:
            tenant.phone_no = data.phone_no
        if data.email is not None:
            tenant.email = str(data.email)
        if data.address is not None:
            tenant.address = data.address
        if data.district is not None:
            tenant.district = data.district
        if data.pincode is not None:
            tenant.pincode = data.pincode

        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def patch_tenant_status(
        self, db: AsyncSession, tenant_id: uuid.UUID, data: TenantStatusPatch
    ) -> Tenant | None:
        tenant = await self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None

        if data.is_verified is not None:
            tenant.is_verified = data.is_verified

        if data.is_active is not None:
            tenant.is_active = data.is_active
            # If deactivated, invalidate all sessions belonging to the tenant
            if not data.is_active:
                await session_service.invalidate_tenant_sessions(tenant_id)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def delete_tenant(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        deleted_by: uuid.UUID | None = None,
    ) -> bool:
        tenant = await self.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False

        tenant.is_deleted = True
        tenant.is_active = False
        tenant.deleted_at = datetime.now(timezone.utc)
        tenant.deleted_by = deleted_by

        # Invalidate all tenant sessions in Redis
        await session_service.invalidate_tenant_sessions(tenant_id)

        await db.commit()
        return True

    # -------------------------------------------------------------
    # Tenant User Operations (scoped by tenant_id)
    # -------------------------------------------------------------
    async def list_tenant_users(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        stmt = (
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_deleted == deleted,
            )
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list((await db.execute(stmt)).scalars().all())

    async def get_tenant_user_by_id(
        self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> User | None:
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.id == user_id,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def create_tenant_user(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        data: TenantUserCreate,
        creator_id: uuid.UUID | None = None,
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            full_name=data.full_name,
            user_name=data.user_name,
            email=str(data.email),
            phone=data.phone,
            role=data.role,
            hashed_password=get_password_hash(data.password),
            is_active=data.is_active,
            is_deleted=False,
            created_by=creator_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_tenant_user(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: TenantUserUpdate,
    ) -> User | None:
        user = await self.get_tenant_user_by_id(db, tenant_id, user_id)
        if not user or user.is_deleted:
            return None

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.user_name is not None:
            user.user_name = data.user_name
        if data.email is not None:
            user.email = str(data.email)
        if data.phone is not None:
            user.phone = data.phone
        if data.role is not None:
            user.role = data.role

        # Invalidate active sessions since user profile changed
        await session_service.invalidate_user_sessions(user_id)

        await db.commit()
        await db.refresh(user)
        return user

    async def patch_tenant_user(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: TenantUserPatch,
    ) -> User | None:
        user = await self.get_tenant_user_by_id(db, tenant_id, user_id)
        if not user or user.is_deleted:
            return None

        if data.password:
            user.hashed_password = get_password_hash(data.password)

        if data.is_active is not None:
            user.is_active = data.is_active

        # Invalidate sessions whenever password or status changes
        await session_service.invalidate_user_sessions(user_id)

        await db.commit()
        await db.refresh(user)
        return user

    async def delete_tenant_user(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        deleter_id: uuid.UUID | None = None,
    ) -> bool:
        user = await self.get_tenant_user_by_id(db, tenant_id, user_id)
        if not user or user.is_deleted:
            return False

        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.deleted_by = deleter_id

        # Invalidate sessions for deleted user
        await session_service.invalidate_user_sessions(user_id)

        await db.commit()
        return True


tenant_service = TenantService()
