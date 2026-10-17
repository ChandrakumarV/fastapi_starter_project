"""Pydantic schemas for request validation and response serialization."""
from fastapi_starter_project.schemas.auth import LoginRequest, TokenPayload
from fastapi_starter_project.schemas.common import HealthResponse, MessageResponse
from fastapi_starter_project.schemas.user import UserInDB, UserResponse

__all__ = [
    "LoginRequest",
    "TokenPayload",
    "HealthResponse",
    "MessageResponse",
    "UserResponse",
    "UserInDB",
]
