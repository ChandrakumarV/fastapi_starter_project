from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


from fastapi_starter_project.models.enums import UserRole


class PlatformUserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_USER = "platform_user"


class UserBase(BaseModel):
    username: str = Field(..., examples=["admin"])
    email: EmailStr = Field(..., examples=["admin@example.com"])
    full_name: str = Field(..., examples=["Platform Admin"])
    role: str = Field(default=UserRole.PLATFORM_USER.value, examples=[UserRole.PLATFORM_USER.value])
    tenant_id: uuid.UUID | None = None
    created_by_id: uuid.UUID | None = None
    is_active: bool = Field(default=True, examples=[True])
    is_deleted: bool = Field(default=False, examples=[False])
    deleted_at: datetime | None = Field(default=None, examples=[None])


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class UserCreateAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["newuser"])
    email: EmailStr = Field(..., examples=["newuser@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New Platform User"])
    password: str = Field(..., min_length=6, examples=["securepassword123"])
    role: PlatformUserRole = Field(
        default=PlatformUserRole.PLATFORM_USER,
        examples=[PlatformUserRole.PLATFORM_USER],
    )


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Updated Name"])
    email: EmailStr | None = Field(default=None, examples=["updated@example.com"])
    password: str | None = Field(default=None, min_length=6, examples=["newsecurepassword123"])


class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Set active status for the user", examples=[False])


class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    hashed_password: str = ""
