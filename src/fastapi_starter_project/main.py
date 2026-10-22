import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from fastapi_starter_project.api.v1.endpoints import health
from fastapi_starter_project.api.v1.router import api_v1_router
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.database import async_engine
from fastapi_starter_project.core.redis import close_redis, get_redis

logger = logging.getLogger("fastapi_starter_project")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # --- Startup ---
    logger.info("Checking database connection...")
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("PostgreSQL database connection established successfully.")
    except Exception as exc:
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        raise exc

    try:
        redis_client = get_redis()
        await redis_client.ping()
        logger.info("Redis connection established successfully.")
    except Exception as exc:
        logger.warning("Failed to connect to Redis: %s", exc)

    yield

    # --- Shutdown ---
    logger.info("Closing database connection pool...")
    await async_engine.dispose()
    logger.info("Database connection pool closed successfully.")

    logger.info("Closing Redis connection pool...")
    await close_redis()
    logger.info("Redis connection pool closed successfully.")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Root welcome route
    @application.get("/", tags=["Root"], include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    # Mount unversioned public health endpoint: /health
    application.include_router(health.router, tags=["Health"])

    # Mount /platform base prefix (Platform Management)
    from fastapi_starter_project.api.v1.endpoints import platform
    application.include_router(platform.router)

    # Mount versioned API router: /api/v1/...
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
