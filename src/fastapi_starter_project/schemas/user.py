from datetime import datetime
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


from fastapi_starter_project.models.enums import UserRole


class PlatformUserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_USER = "platform_user"


class UserBase(BaseModel):
    username: str = Field(..., examples=["admin"])
    email: EmailStr = Field(..., examples=["admin@example.com"])
    full_name: str = Field(..., examples=["Platform Admin"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    role: str = Field(default=UserRole.PLATFORM_USER.value, examples=[UserRole.PLATFORM_USER.value])
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
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    password: str = Field(..., min_length=6, examples=["securepassword123"])
    role: PlatformUserRole = Field(
        default=PlatformUserRole.PLATFORM_USER,
        examples=[PlatformUserRole.PLATFORM_USER],
    )


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Updated Name"])
    email: EmailStr | None = Field(default=None, examples=["updated@example.com"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    password: str | None = Field(default=None, min_length=6, examples=["newsecurepassword123"])


class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Set active status for the user", examples=[False])


class UserAdminUpdate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["newuser"])
    email: EmailStr = Field(..., examples=["newuser@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New Platform User"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    role: PlatformUserRole = Field(
        default=PlatformUserRole.PLATFORM_USER,
        examples=[PlatformUserRole.PLATFORM_USER],
    )


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=1, examples=["oldpassword123"])
    new_password: str = Field(..., min_length=6, examples=["newpassword123"])
    confirm_new_password: str = Field(..., min_length=6, examples=["newpassword123"])

    @model_validator(mode="before")
    @classmethod
    def handle_confirm_typo(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "comfirm_new_password" in data and "confirm_new_password" not in data:
                data["confirm_new_password"] = data["comfirm_new_password"]
        return data

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserPasswordUpdate":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New password and confirmation password do not match.")
        return self


class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    hashed_password: str = ""
