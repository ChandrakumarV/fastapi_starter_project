from fastapi import APIRouter
from fastapi_starter_project.api.v1.endpoints import admin, user

api_v1_router = APIRouter()

# User endpoints
api_v1_router.include_router(user.router)

# Admin endpoints (/admin/...)
api_v1_router.include_router(admin.router)
