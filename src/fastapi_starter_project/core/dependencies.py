from typing import Annotated
from fastapi import Cookie, HTTPException, status
import jwt
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.security import decode_access_token
from fastapi_starter_project.schemas.user import UserInDB
from fastapi_starter_project.services.user_service import user_service


def get_current_user(
    access_token: Annotated[str | None, Cookie(alias=settings.COOKIE_NAME)] = None,
) -> UserInDB:
    """
    Extracts and verifies JWT from the HTTP-only cookie.
    Retrieves the corresponding user from user_service.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing access token cookie.",
        )

    try:
        payload = decode_access_token(access_token)
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject identifier.",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    user = user_service.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user
