import asyncio
import uuid
from sqlalchemy import select
from fastapi_starter_project.core.database import async_session_maker
from fastapi_starter_project.core.security import get_password_hash
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.models.tenant import Tenant
from fastapi_starter_project.models.user import User


async def seed_initial_data() -> None:
    """Seed initial platform super admin, sample tenant, and tenant users."""
    async with async_session_maker() as session:
        # 1. Platform Admin
        admin_stmt = select(User).where(User.user_name == "admin")
        super_admin = (await session.execute(admin_stmt)).scalar_one_or_none()
        if not super_admin:
            admin_id = uuid.uuid4()
            super_admin = User(
                id=admin_id,
                full_name="Platform Admin",
                user_name="admin",
                email="admin@example.com",
                phone="9876543200",
                role=UserRole.PLATFORM_ADMIN.value,
                is_active=True,
                created_by=admin_id,
                hashed_password=get_password_hash("password"),
            )
            session.add(super_admin)
            await session.flush()
            print("[Seed] Created platform_admin: admin")
        else:
            super_admin.role = UserRole.PLATFORM_ADMIN.value
            if not super_admin.created_by or super_admin.created_by != super_admin.id:
                super_admin.created_by = super_admin.id
            await session.flush()
            print("[Seed] platform_admin updated")

        # 2. Sample Tenant
        tenant_stmt = select(Tenant).where(Tenant.name == "ABC Exports")
        tenant = (await session.execute(tenant_stmt)).scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name="ABC Exports",
                phone_no="9876543210",
                email="contact@example.com",
                address="123 Main Road",
                district="Karur",
                pincode=639001,
                is_verified=True,
                is_active=True,
                created_by=super_admin.id,
            )
            session.add(tenant)
            await session.flush()
            print(f"[Seed] Created sample tenant: {tenant.name} (id={tenant.id})")
        else:
            print(f"[Seed] Tenant {tenant.name} already exists")

        # 3. Tenant Admin
        t_admin_stmt = select(User).where(User.user_name == "abc_admin")
        t_admin = (await session.execute(t_admin_stmt)).scalar_one_or_none()
        if not t_admin:
            t_admin = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                full_name="Tenant Admin",
                user_name="abc_admin",
                email="tenant_admin@example.com",
                phone="9876543211",
                role=UserRole.TENANT_ADMIN.value,
                is_active=True,
                created_by=super_admin.id,
                hashed_password=get_password_hash("password"),
            )
            session.add(t_admin)
            print("[Seed] Created tenant_admin: abc_admin")
        else:
            print("[Seed] tenant_admin already exists")

        # 4. Tenant User
        t_user_stmt = select(User).where(User.user_name == "abc_user")
        t_user = (await session.execute(t_user_stmt)).scalar_one_or_none()
        if not t_user:
            t_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                full_name="Tenant User",
                user_name="abc_user",
                email="tenant_user@example.com",
                phone="9876543212",
                role=UserRole.TENANT_USER.value,
                is_active=True,
                created_by=t_admin.id if t_admin else super_admin.id,
                hashed_password=get_password_hash("password"),
            )
            session.add(t_user)
            print("[Seed] Created tenant_user: abc_user")
        else:
            print("[Seed] tenant_user already exists")

        await session.commit()
    print("[Seed] Seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_initial_data())
