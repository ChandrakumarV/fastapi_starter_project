import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.models.user import User


@pytest.mark.anyio
async def test_database_connection_and_user_query() -> None:
    test_engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.username == "admin"
        assert user.email == "admin@example.com"
        assert user.role == "admin"

    await test_engine.dispose()
