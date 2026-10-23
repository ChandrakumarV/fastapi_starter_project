from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from fastapi_starter_project.schemas.common import validate_username


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=50, examples=["johndoe"])
    password: str = Field(..., min_length=4, examples=["password123"])


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=50, examples=["newuser"])
    email: EmailStr = Field(..., examples=["newuser@example.com"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["New User"])
    password: str = Field(..., min_length=6, examples=["securepassword123"])

    @field_validator("username")
    @classmethod
    def validate_register_username(cls, v: str) -> str:
        return validate_username(v)


class UsernameAvailabilityResponse(BaseModel):
    username: str = Field(..., examples=["john_doe"])
    available: bool = Field(..., examples=[True])
    message: str = Field(..., examples=["Username is available."])


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=1, examples=["admin"])
    password: str = Field(..., min_length=4, examples=["password"])


class TokenPayload(BaseModel):
    sub: str
    role: str | None = None
    tenant_id: str | None = None
    session_id: str | None = None
    exp: datetime
    iat: datetime
