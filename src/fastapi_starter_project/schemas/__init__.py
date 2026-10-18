"""Pydantic schemas for request validation and response serialization."""
from fastapi_starter_project.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenPayload,
    UsernameAvailabilityResponse,
)
from fastapi_starter_project.schemas.common import (
    DatabaseHealth,
    HealthResponse,
    MessageResponse,
    ServerHealth,
)
from fastapi_starter_project.schemas.user import (
    UserBase,
    UserCreateAdmin,
    UserInDB,
    UserResponse,
    UserRole,
    UserStatusUpdate,
    UserUpdate,
)

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "UsernameAvailabilityResponse",
    "TokenPayload",
    "HealthResponse",
    "ServerHealth",
    "DatabaseHealth",
    "MessageResponse",
    "UserBase",
    "UserResponse",
    "UserRole",
    "UserCreateAdmin",
    "UserUpdate",
    "UserStatusUpdate",
    "UserInDB",
]
