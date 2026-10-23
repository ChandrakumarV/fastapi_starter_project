import re
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

USERNAME_REGEX = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_username(v: str | None) -> str | None:
    """
    Validates username rules:
    - Must be lowercase only.
    - Only lowercase letters, numbers, and underscore are allowed.
    - Must not start with an underscore or number (must start with a-z).
    - Length between 3 and 50 characters.
    """
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("Username must be a string.")

    if len(v) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if len(v) > 50:
        raise ValueError("Username cannot exceed 50 characters.")

    if v[0] == "_":
        raise ValueError("Username cannot start with an underscore ('_'). It must start with a lowercase letter.")
    if v[0].isdigit():
        raise ValueError("Username cannot start with a number. It must start with a lowercase letter.")
    if not ("a" <= v[0] <= "z"):
        raise ValueError("Username must start with a lowercase letter (a-z).")

    if any(c.isupper() for c in v):
        raise ValueError("Username must be in lowercase only.")

    if not USERNAME_REGEX.match(v):
        raise ValueError(
            "Username can only contain lowercase letters, numbers, and underscores ('_'). No spaces or other special characters allowed."
        )

    return v


class MessageResponse(BaseModel):
    message: str = Field(..., examples=["Operation completed successfully"])


class ServerHealth(BaseModel):
    status: str = Field(default="healthy", examples=["healthy"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["development"])


class DatabaseHealth(BaseModel):
    status: str = Field(..., examples=["connected"])
    details: str = Field(..., examples=["PostgreSQL responding normally"])


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", examples=["healthy"])
    timestamp: datetime = Field(..., examples=["2026-10-17T14:30:00Z"])
    server: ServerHealth
    database: DatabaseHealth


class UserAuditBrief(BaseModel):
    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)
