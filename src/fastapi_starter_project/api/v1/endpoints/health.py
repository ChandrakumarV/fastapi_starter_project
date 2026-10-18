from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import get_db
from fastapi_starter_project.schemas.common import DatabaseHealth, HealthResponse, ServerHealth

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns server health and database connectivity health.",
)
async def get_health(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthResponse:
    db_status = "connected"
    db_details = "PostgreSQL is reachable and responding to queries."
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "disconnected"
        db_details = f"Database error: {exc}"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        server=ServerHealth(
            status="healthy",
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        ),
        database=DatabaseHealth(
            status=db_status,
            details=db_details,
        ),
    )
