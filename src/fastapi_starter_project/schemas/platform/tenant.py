from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from fastapi_starter_project.schemas.common import UserAuditBrief, validate_username


class TenantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=100, examples=["ABC Exports"])
    phone_no: str = Field(..., min_length=10, max_length=10, examples=["9876543210"])
    email: EmailStr = Field(..., examples=["contact@example.com"])
    address: str = Field(..., min_length=2, max_length=255, examples=["123 Main Road"])
    district: str = Field(..., min_length=2, max_length=100, examples=["Karur"])
    pincode: int = Field(..., gt=0, examples=[639001])
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    user_name: str = Field(..., min_length=2, max_length=100, examples=["Tenant Admin"])
    user_id_name: str = Field(..., min_length=3, max_length=50, examples=["abc_admin"])
    user_email: EmailStr = Field(..., examples=["admin@example.com"])
    user_phone: str = Field(..., min_length=10, max_length=10, examples=["9876543211"])
    password: str = Field(..., min_length=6, examples=["password"])
    confirm_password: str = Field(..., min_length=6, examples=["password"])

    @field_validator("user_id_name")
    @classmethod
    def validate_tenant_admin_username(cls, v: str) -> str:
        return validate_username(v)

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "TenantCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class TenantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone_no: str | None = Field(default=None, min_length=10, max_length=10)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=2, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: int | None = Field(default=None, gt=0)


class TenantStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool | None = None
    is_verified: bool | None = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    name: str
    phone_no: str
    email: str
    address: str
    district: str
    pincode: int
    is_verified: bool
    is_active: bool
    is_deleted: bool = False
    deleted_at: datetime | None = None
    created_by: UserAuditBrief | None = None
    deleted_by: UserAuditBrief | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_audit_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        deleted_by_obj = None
        if getattr(data, "deleted_by_user", None):
            deleted_by_obj = UserAuditBrief(id=data.deleted_by_user.id, name=data.deleted_by_user.name)
        elif getattr(data, "deleted_by", None):
            deleted_by_obj = UserAuditBrief(id=data.deleted_by, name="Platform Admin")

        created_by_obj = None
        if getattr(data, "created_by_user", None):
            created_by_obj = UserAuditBrief(id=data.created_by_user.id, name=data.created_by_user.name)
        elif getattr(data, "created_by", None):
            created_by_obj = UserAuditBrief(id=data.created_by, name="Platform Admin")

        return {
            "id": getattr(data, "id"),
            "created_at": getattr(data, "created_at"),
            "name": getattr(data, "name"),
            "phone_no": getattr(data, "phone_no"),
            "email": getattr(data, "email"),
            "address": getattr(data, "address"),
            "district": getattr(data, "district"),
            "pincode": getattr(data, "pincode"),
            "is_verified": getattr(data, "is_verified"),
            "is_active": getattr(data, "is_active"),
            "is_deleted": getattr(data, "is_deleted", False),
            "deleted_at": getattr(data, "deleted_at", None),
            "created_by": created_by_obj,
            "deleted_by": deleted_by_obj,
        }
