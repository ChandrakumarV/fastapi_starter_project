from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.security import decode_access_token
from fastapi_starter_project.schemas.user import UserInDB
from fastapi_starter_project.services.user_service import user_service


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie(alias=settings.COOKIE_NAME)] = None,
    auth_header: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> UserInDB:
    """
    Extracts and verifies JWT from Authorization header (Bearer) or HTTP-only cookie.
    Retrieves the corresponding user from the database.
    """
    token: str | None = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing access token.",
        )

    try:
        payload = decode_access_token(token)
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

    user = await user_service.get_by_username(db=db, username=username)
    if not user or user.is_deleted:
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


async def require_admin(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Dependency that restricts access exclusively to users with the 'admin' role."""
    role_value = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


async def require_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Dependency that restricts access exclusively to users with the 'user' role."""
    role_value = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_value != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required.",
        )
    return current_user
