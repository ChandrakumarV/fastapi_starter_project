from datetime import datetime, timezone
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.security import get_password_hash, verify_password
from fastapi_starter_project.models.user import User
from fastapi_starter_project.schemas.user import UserInDB, UserUpdate


class UserService:
    """User service handling user database operations with PostgreSQL."""

    def _to_user_in_db(self, user: User) -> UserInDB:
        return UserInDB(
            id=user.id,
            username=user.user_name,
            email=user.email,
            full_name=user.name,
            phone=user.phone,
            role=user.role,
            tenant_id=user.tenant_id,
            created_by_id=user.created_by_id,
            is_active=user.is_active,
            is_deleted=user.is_deleted,
            deleted_at=user.deleted_at,
            hashed_password=user.hashed_password,
        )

    async def get_by_username(
        self, db: AsyncSession, username: str
    ) -> UserInDB | None:
        result = await db.execute(select(User).where(User.user_name == username))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_user_in_db(db_user)

    async def get_by_email(
        self, db: AsyncSession, email: str
    ) -> UserInDB | None:
        result = await db.execute(select(User).where(User.email == email))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_user_in_db(db_user)

    async def get_by_email_or_username(
        self, db: AsyncSession, identifier: str
    ) -> UserInDB | None:
        stmt = select(User).where(
            or_(User.email == identifier, User.user_name == identifier)
        )
        db_user = (await db.execute(stmt)).scalar_one_or_none()
        if not db_user:
            return None
        return self._to_user_in_db(db_user)

    async def get_by_id(
        self, db: AsyncSession, user_id: uuid.UUID | str
    ) -> UserInDB | None:
        u_id = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        result = await db.execute(select(User).where(User.id == u_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_user_in_db(db_user)

    async def list_users(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        roles: list[str] | None = None,
    ) -> list[UserInDB]:
        query = select(User)
        if not include_deleted:
            query = query.where(User.is_deleted == False)
        if roles is not None:
            query = query.where(User.role.in_(roles))

        result = await db.execute(query.offset(skip).limit(limit))
        db_users = result.scalars().all()
        return [self._to_user_in_db(u) for u in db_users]

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        full_name: str,
        password: str,
        role: str = "tenant_user",
        tenant_id: uuid.UUID | None = None,
        created_by_id: uuid.UUID | None = None,
        phone: str | None = None,
    ) -> UserInDB:
        hashed_pw = get_password_hash(password)
        new_user = User(
            id=uuid.uuid4(),
            user_name=username,
            email=email,
            name=full_name,
            phone=phone,
            hashed_password=hashed_pw,
            role=role,
            tenant_id=tenant_id,
            created_by_id=created_by_id,
            is_active=True,
            is_deleted=False,
            deleted_at=None,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return self._to_user_in_db(new_user)

    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        required_role: str | None = None,
    ) -> UserInDB | None:
        user = await self.get_by_email_or_username(db, username)
        if not user or user.is_deleted:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if required_role and user.role != required_role:
            return None
        return user

    async def update_user(
        self, db: AsyncSession, user_id: uuid.UUID | str, update_data: UserUpdate
    ) -> UserInDB | None:
        u_id = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        result = await db.execute(select(User).where(User.id == u_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None

        if update_data.full_name is not None:
            db_user.name = update_data.full_name
        if update_data.email is not None:
            db_user.email = update_data.email
        if update_data.phone is not None:
            db_user.phone = update_data.phone
        if update_data.password is not None:
            db_user.hashed_password = get_password_hash(update_data.password)

        await db.commit()
        await db.refresh(db_user)
        return self._to_user_in_db(db_user)

    async def set_user_active_status(
        self, db: AsyncSession, user_id: uuid.UUID | str, is_active: bool
    ) -> UserInDB | None:
        u_id = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        result = await db.execute(select(User).where(User.id == u_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None

        db_user.is_active = is_active
        await db.commit()
        await db.refresh(db_user)
        return self._to_user_in_db(db_user)

    async def delete_user(self, db: AsyncSession, user_id: uuid.UUID | str) -> bool:
        u_id = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        result = await db.execute(select(User).where(User.id == u_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return False

        db_user.is_deleted = True
        db_user.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True


user_service = UserService()
