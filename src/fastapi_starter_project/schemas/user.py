from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., examples=["johndoe"])
    email: EmailStr = Field(..., examples=["johndoe@example.com"])
    full_name: str = Field(..., examples=["John Doe"])
    role: str = Field(default="user", examples=["admin"])
    is_active: bool = Field(default=True)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., examples=[1])


class UserInDB(UserBase):
    id: int
    hashed_password: str
