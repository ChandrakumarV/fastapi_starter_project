from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_starter_project.api.v1.endpoints import auth, health, users
from fastapi_starter_project.api.v1.router import api_v1_router
from fastapi_starter_project.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions (e.g., database connection pool initialization)
    yield
    # Shutdown actions (e.g., closing connections)


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

    # Mount versioned API router: /api/v1/...
    application.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Mount root aliases for convenience (/health, /login, /logout, /me)
    application.include_router(health.router, tags=["Health"], include_in_schema=False)
    application.include_router(auth.router, tags=["Authentication"], include_in_schema=False)
    application.include_router(users.router, tags=["Users"], include_in_schema=False)

    return application


app = create_application()
