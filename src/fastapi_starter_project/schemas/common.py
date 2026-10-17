from datetime import datetime
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str = Field(..., examples=["Operation completed successfully"])


class HealthResponse(BaseModel):
    status: str = Field("healthy", examples=["healthy"])
    timestamp: datetime = Field(..., examples=["2026-10-16T15:30:00Z"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["development"])
