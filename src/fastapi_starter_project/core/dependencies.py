from typing import Annotated
import uuid
from fastapi import Cookie, Depends, HTTPException, status
import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.core.security import decode_access_token
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.schemas.user import UserInDB
from fastapi_starter_project.services.session_service import session_service
from fastapi_starter_project.services.tenant_service import tenant_service
from fastapi_starter_project.services.user_service import user_service


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie(alias=settings.COOKIE_NAME)] = None,
) -> UserInDB:
    """
    Extracts and verifies JWT from HTTP-only cookie.
    Validates Redis session for platform users (platform_admin, platform_user)
    and tenant users (tenant_admin, tenant_user).
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing access token.",
        )

    token = access_token

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    username: str = payload.sub
    role: str | None = payload.role
    session_id: str | None = payload.session_id

    # Fast-path: Check active Redis session first.
    # When a session is active, user and tenant validity are already guaranteed in memory,
    # avoiding redundant PostgreSQL queries on every single request.
    if session_id:
        session_data = await session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again.",
            )
        if session_data.get("username") and session_data.get("user_id"):
            if not session_data.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user account.",
                )
            return UserInDB(
                id=uuid.UUID(str(session_data["user_id"])),
                username=session_data["username"],
                email=session_data.get("email", f"{session_data['username']}@example.com"),
                full_name=session_data.get("full_name", session_data["username"]),
                phone=session_data.get("phone"),
                role=session_data.get("role", role or UserRole.PLATFORM_USER.value),
                tenant_id=uuid.UUID(str(session_data["tenant_id"])) if session_data.get("tenant_id") else None,
                created_by_id=uuid.UUID(str(session_data["created_by_id"])) if session_data.get("created_by_id") else None,
                is_active=session_data.get("is_active", True),
                is_deleted=False,
            )

    platform_roles = (
        UserRole.PLATFORM_ADMIN.value,
        UserRole.PLATFORM_USER.value,
    )
    tenant_roles = (
        UserRole.TENANT_ADMIN.value,
        UserRole.TENANT_USER.value,
    )

    # Active session is mandatory for both platform users and tenant users
    if role in platform_roles or role in tenant_roles:
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again.",
            )

    # Fallback to database only if session is missing cached fields (e.g. simulated tokens in unit tests)
    user = await user_service.get_by_email_or_username(db=db, identifier=username)
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

    # If the user belongs to a tenant, check if the tenant is active
    if user.tenant_id:
        tenant = await tenant_service.get_tenant_by_id(db, user.tenant_id)
        if not tenant or not tenant.is_active or tenant.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant account is inactive or disabled.",
            )

    return user


def is_platform_admin(user: UserInDB) -> bool:
    """Checks if user is a Platform Admin (top-level system admin)."""
    role_value = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )
    if role_value == UserRole.PLATFORM_ADMIN.value:
        if not user.tenant_id:
            return True
    if not user.tenant_id and user.created_by_id and user.created_by_id == user.id:
        return True
    return False


def is_platform_user(user: UserInDB) -> bool:
    """Checks if user is a Platform User (operator staff user on the platform, formerly platform_admin)."""
    role_value = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )
    if role_value == UserRole.PLATFORM_USER.value:
        return True
    if not user.tenant_id and user.created_by_id and user.created_by_id != user.id:
        return True
    return False


def is_platform_member(user: UserInDB) -> bool:
    """Checks if user has any platform role (platform_admin or platform_user)."""
    return is_platform_admin(user) or is_platform_user(user)


def is_tenant_admin(user: UserInDB) -> bool:
    """Checks if user is an administrator within their tenant."""
    role_value = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )
    return role_value == UserRole.TENANT_ADMIN.value and user.tenant_id is not None


def is_tenant_user(user: UserInDB) -> bool:
    """Checks if user is a regular tenant member."""
    role_value = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )
    return role_value == UserRole.TENANT_USER.value and user.tenant_id is not None


async def require_platform_admin(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Restricts access strictly to Platform Administrators (top-level platform admins)."""
    if not is_platform_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin privileges required.",
        )
    return current_user


async def require_platform_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Restricts access strictly to Platform Users."""
    if not is_platform_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform user privileges required.",
        )
    return current_user


async def require_platform_access(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Allows access to both Platform Admins and Platform Users."""
    if not is_platform_member(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform access required.",
        )
    return current_user


async def require_tenant_admin(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Restricts access to Tenant Administrators (or Platform Admins with global override)."""
    if is_tenant_admin(current_user) or is_platform_admin(current_user):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tenant admin privileges required.",
    )


async def require_tenant_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Restricts access to Tenant Users."""
    if is_tenant_user(current_user) or is_tenant_admin(current_user) or is_platform_admin(current_user):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tenant user access required.",
    )


async def require_tenant_access(
    tenant_id: uuid.UUID,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """
    Enforces authorization for tenant resources:
    - Platform admins and platform users can manage across any tenant.
    - Tenant admins and tenant users can only access their own tenant.
    """
    if is_platform_member(current_user):
        return current_user

    if is_tenant_admin(current_user) or is_tenant_user(current_user):
        if current_user.tenant_id == tenant_id:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only access resources within your own tenant.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tenant access privileges required.",
    )


async def require_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    """Generic user requirement. Rejects platform accounts."""
    if is_platform_member(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required.",
        )
    return current_user
