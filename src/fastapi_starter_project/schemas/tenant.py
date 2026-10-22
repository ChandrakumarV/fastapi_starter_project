from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["ABC Exports"])
    phone_no: str = Field(..., min_length=7, max_length=20, examples=["9876543210"])
    email: EmailStr = Field(..., examples=["contact@example.com"])
    address: str = Field(..., min_length=2, max_length=255, examples=["123 Main Road"])
    district: str = Field(..., min_length=2, max_length=100, examples=["Karur"])
    pincode: int = Field(..., gt=0, examples=[639001])
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    user_name: str = Field(..., min_length=2, max_length=100, examples=["Tenant Admin"])
    user_id_name: str = Field(..., min_length=3, max_length=50, examples=["abc_admin"])
    user_email: EmailStr = Field(..., examples=["admin@example.com"])
    user_phone: str = Field(..., min_length=7, max_length=20, examples=["9876543211"])
    password: str = Field(..., min_length=6, examples=["password"])
    confirm_password: str = Field(..., min_length=6, examples=["password"])

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "TenantCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone_no: str | None = Field(default=None, min_length=7, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=2, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: int | None = Field(default=None, gt=0)


class TenantStatusPatch(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)
