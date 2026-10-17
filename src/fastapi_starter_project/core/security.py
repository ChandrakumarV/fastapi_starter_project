from datetime import datetime, timedelta, timezone
import secrets
from typing import Any
import jwt
from fastapi_starter_project.core.config import settings


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes JWT and validates signature and expiration."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


def verify_password(plain_password: str, hashed_or_stored_password: str) -> bool:
    """
    Constant-time password comparison.
    Can be swapped with passlib/pwdlib (bcrypt or argon2) when integrating a database.
    """
    return secrets.compare_digest(plain_password, hashed_or_stored_password)
