from datetime import datetime
from typing import Any, Literal
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from fastapi_starter_project.schemas.common import UserAuditBrief, validate_username


class TenantUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    user_name: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    phone: str = Field(..., min_length=10, max_length=10, examples=["9876543212"])
    role: Literal["tenant_admin", "tenant_user"] = Field(
        default="tenant_user", examples=["tenant_user"]
    )
    is_active: bool = Field(default=True)
    password: str = Field(..., min_length=6, examples=["password"])
    confirm_password: str = Field(..., min_length=6, examples=["password"])

    @field_validator("user_name")
    @classmethod
    def validate_tenant_username(cls, v: str) -> str:
        return validate_username(v)

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "TenantUserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class TenantUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    user_name: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=10)
    role: Literal["tenant_admin", "tenant_user"] | None = None

    @field_validator("user_name", mode="before")
    @classmethod
    def empty_username_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("user_name")
    @classmethod
    def validate_tenant_username_update(cls, v: str | None) -> str | None:
        return validate_username(v)


class TenantUserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str | None = Field(default=None, min_length=6)
    confirm_password: str | None = Field(default=None, min_length=6)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> "TenantUserPatch":
        if self.password is not None or self.confirm_password is not None:
            if not self.password or not self.confirm_password:
                raise ValueError("Both password and confirm_password must be provided.")
            if self.password != self.confirm_password:
                raise ValueError("Passwords do not match.")
        return self


class TenantUserResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    created_by: UserAuditBrief | None = None
    full_name: str
    user_name: str
    email: str
    phone: str | None = None
    role: str
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None = None
    deleted_by: UserAuditBrief | None = None

    model_config = ConfigDict(from_attributes=True)
