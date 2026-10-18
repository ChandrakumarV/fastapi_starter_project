import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.database import async_session_maker
from fastapi_starter_project.core.security import verify_password
from fastapi_starter_project.models.user import User


async def seed_initial_data() -> None:
    """Seed initial admin and test users if they do not exist."""
    initial_users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "role": "admin",
            "is_active": True,
            "hashed_password": "password123",
        },
        {
            "username": "user",
            "email": "user@example.com",
            "full_name": "Normal User",
            "role": "user",
            "is_active": True,
            "hashed_password": "password456",
        },
    ]

    async with async_session_maker() as session:
        for user_data in initial_users:
            stmt = select(User).where(User.username == user_data["username"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                new_user = User(**user_data)
                session.add(new_user)
                print(f"[Seed] Created user: {user_data['username']}")
            else:
                print(f"[Seed] User already exists: {user_data['username']}")
        await session.commit()
    print("[Seed] Seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_initial_data())
