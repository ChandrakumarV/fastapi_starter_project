from fastapi_starter_project.core.security import verify_password
from fastapi_starter_project.schemas.user import UserInDB


class UserService:
    """
    User service handling user operations.
    Currently backed by an in-memory/dummy data store, easily replaceable
    with an ORM (SQLAlchemy, SQLModel, Tortoise) in production.
    """

    def __init__(self) -> None:
        # Dummy in-memory users store
        self._users: dict[str, UserInDB] = {
            "johndoe": UserInDB(
                id=1,
                username="johndoe",
                email="johndoe@example.com",
                full_name="John Doe",
                role="admin",
                is_active=True,
                hashed_password="password123",  # In real production with DB, store argon2/bcrypt hash
            ),
            "janedoe": UserInDB(
                id=2,
                username="janedoe",
                email="janedoe@example.com",
                full_name="Jane Doe",
                role="user",
                is_active=True,
                hashed_password="password456",
            ),
        }

    def get_by_username(self, username: str) -> UserInDB | None:
        return self._users.get(username)

    def get_by_id(self, user_id: int) -> UserInDB | None:
        for user in self._users.values():
            if user.id == user_id:
                return user
        return None

    def authenticate(self, username: str, password: str) -> UserInDB | None:
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


# Singleton instance
user_service = UserService()
