from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
from typing import Any
import jwt
from fastapi_starter_project.core.config import settings


def get_password_hash(password: str) -> str:
    """Generates a secure salted PBKDF2 SHA-256 password hash."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_or_stored_password: str) -> bool:
    """
    Verifies a plain password against the stored password hash.
    Supports PBKDF2 hashes and constant-time string comparison for dev/seeded accounts.
    """
    if hashed_or_stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, salt_hex, key_hex = hashed_or_stored_password.split("$")
            salt = bytes.fromhex(salt_hex)
            key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
            return secrets.compare_digest(key.hex(), key_hex)
        except Exception:
            return False
    return secrets.compare_digest(plain_password, hashed_or_stored_password)


def create_access_token(
    subject: str | Any,
    role: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
    }
    if role:
        to_encode["role"] = role

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes JWT and validates signature and expiration."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
