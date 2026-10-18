from fastapi import APIRouter
from fastapi_starter_project.api.v1.endpoints import admin, auth, me

api_v1_router = APIRouter()

# Authentication & Registration
api_v1_router.include_router(auth.router)

# User endpoints (/me, etc.)
api_v1_router.include_router(me.router)

# Admin endpoints (/admin/auth/..., /admin/me, /admin/users)
api_v1_router.include_router(admin.router)
