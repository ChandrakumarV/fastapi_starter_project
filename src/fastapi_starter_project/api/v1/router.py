from fastapi import APIRouter
from fastapi_starter_project.api.v1.endpoints import auth, health, users

api_v1_router = APIRouter()

# Public endpoints
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, tags=["Authentication"])

# Protected endpoints
api_v1_router.include_router(users.router, tags=["Users"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"], include_in_schema=False)
