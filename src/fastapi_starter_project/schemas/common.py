from datetime import datetime
from pydantic import BaseModel, Field


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
