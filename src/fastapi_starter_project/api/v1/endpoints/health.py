from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service availability, timestamp, and active environment.",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
