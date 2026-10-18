from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    username: str = Field(..., examples=["johndoe"])
    email: EmailStr = Field(..., examples=["johndoe@example.com"])
    full_name: str = Field(..., examples=["John Doe"])
    role: UserRole = Field(default=UserRole.USER, examples=[UserRole.USER])
    is_active: bool = Field(default=True, examples=[True])
    is_deleted: bool = Field(default=False, examples=[False])
    deleted_at: datetime | None = Field(default=None, examples=[None])


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., examples=[1])


class UserCreateAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["newadmin"])
    email: EmailStr = Field(..., examples=["newadmin@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New Admin"])
    password: str = Field(..., min_length=6, examples=["securepassword123"])
    role: UserRole = Field(default=UserRole.USER, examples=[UserRole.ADMIN])


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100, examples=["Updated Name"])
    email: EmailStr | None = Field(default=None, examples=["updated@example.com"])
    password: str | None = Field(default=None, min_length=6, examples=["newsecurepassword123"])


class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Set active status for the user", examples=[False])


class UserInDB(UserBase):
    id: int
    hashed_password: str
