from datetime import datetime
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from fastapi_starter_project.models.enums import UserRole
from fastapi_starter_project.schemas.common import UserAuditBrief, validate_username


class PlatformUserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_USER = "platform_user"


class UserProfileBase(BaseModel):
    username: str = Field(..., examples=["admin"])
    email: EmailStr = Field(..., examples=["admin@example.com"])
    full_name: str = Field(..., examples=["Platform Admin"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    role: str = Field(default=UserRole.PLATFORM_USER.value, examples=[UserRole.PLATFORM_USER.value])


class UserProfileResponse(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


UserMeResponse = UserProfileResponse


class UserBase(UserProfileBase):
    created_by: uuid.UUID | None = None
    is_active: bool = Field(default=True, examples=[True])
    is_deleted: bool = Field(default=False, examples=[False])
    deleted_at: datetime | None = Field(default=None, examples=[None])
    deleted_by: UserAuditBrief | None = Field(default=None, examples=[None])

    @model_validator(mode="before")
    @classmethod
    def handle_created_by_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "created_by_id" in data and "created_by" not in data:
                data["created_by"] = data["created_by_id"]
        return data

    @property
    def created_by_id(self) -> uuid.UUID | None:
        return self.created_by


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class UserCreateAdmin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=50, examples=["newuser"])
    email: EmailStr = Field(..., examples=["newuser@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New Platform User"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    password: str = Field(..., min_length=6, examples=["securepassword123"])
    role: PlatformUserRole = Field(
        default=PlatformUserRole.PLATFORM_USER,
        examples=[PlatformUserRole.PLATFORM_USER],
    )

    @field_validator("username")
    @classmethod
    def validate_platform_create_username(cls, v: str) -> str:
        return validate_username(v)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Updated Name"])
    username: str | None = Field(default=None, min_length=3, max_length=50, examples=["newusername"])
    email: EmailStr | None = Field(default=None, examples=["updated@example.com"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])

    @field_validator("username", mode="before")
    @classmethod
    def empty_username_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("username")
    @classmethod
    def validate_platform_update_username(cls, v: str | None) -> str | None:
        return validate_username(v)


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool = Field(..., description="Set active status for the user", examples=[False])


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=50, examples=["newuser"])
    email: EmailStr = Field(..., examples=["newuser@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New Platform User"])
    phone: str | None = Field(default=None, min_length=10, max_length=10, examples=["9876543200"])
    role: PlatformUserRole = Field(
        default=PlatformUserRole.PLATFORM_USER,
        examples=[PlatformUserRole.PLATFORM_USER],
    )
    password: str | None = Field(default=None, min_length=6, examples=["newpassword123"])

    @field_validator("password", "phone", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("username")
    @classmethod
    def validate_platform_admin_update_username(cls, v: str) -> str:
        return validate_username(v)


class UserPasswordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
