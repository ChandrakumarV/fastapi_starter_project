from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["johndoe"])
    password: str = Field(..., min_length=4, examples=["password123"])


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime
