from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.security import get_password_hash, verify_password
from fastapi_starter_project.models.user import User
from fastapi_starter_project.schemas.user import UserInDB, UserUpdate


class UserService:
    """
    User service handling user database operations with PostgreSQL.
    Implements soft deletion and active status management.
    """

    def _to_user_in_db(self, user: User) -> UserInDB:
        return UserInDB(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_deleted=user.is_deleted,
            deleted_at=user.deleted_at,
            hashed_password=user.hashed_password,
        )

    async def get_by_username(
        self, db: AsyncSession, username: str
    ) -> UserInDB | None:
        result = await db.execute(select(User).where(User.username == username))
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

    async def get_by_id(
        self, db: AsyncSession, user_id: int
    ) -> UserInDB | None:
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_user_in_db(db_user)

    async def list_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, include_deleted: bool = False
    ) -> list[UserInDB]:
        query = select(User)
        if not include_deleted:
            query = query.where(User.is_deleted == False)

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
        role: str = "user",
    ) -> UserInDB:
        hashed_pw = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_pw,
            role=role,
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
        user = await self.get_by_username(db, username)
        if not user or user.is_deleted:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if required_role and user.role != required_role:
            return None
        return user

    async def update_user(
        self, db: AsyncSession, user_id: int, update_data: UserUpdate
    ) -> UserInDB | None:
        result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None

        if update_data.full_name is not None:
            db_user.full_name = update_data.full_name
        if update_data.email is not None:
            db_user.email = update_data.email
        if update_data.password is not None:
            db_user.hashed_password = get_password_hash(update_data.password)

        await db.commit()
        await db.refresh(db_user)
        return self._to_user_in_db(db_user)

    async def set_user_active_status(
        self, db: AsyncSession, user_id: int, is_active: bool
    ) -> UserInDB | None:
        """Allows administrators to activate or deactivate a user account."""
        result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None

        db_user.is_active = is_active
        await db.commit()
        await db.refresh(db_user)
        return self._to_user_in_db(db_user)

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """
        Performs a soft delete on the user. Never hard deletes rows.
        Marks is_deleted as True and records deleted_at timestamp.
        """
        result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return False

        db_user.is_deleted = True
        db_user.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True


# Singleton instance
user_service = UserService()
