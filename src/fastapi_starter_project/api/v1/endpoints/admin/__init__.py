from fastapi import APIRouter
from fastapi_starter_project.api.v1.endpoints.admin import auth, me, users

router = APIRouter(prefix="/admin")

# Authentication endpoints (/admin/auth/...)
router.include_router(auth.router)

# Profile endpoints (/admin/me)
router.include_router(me.router)

# User management endpoints (/admin/users, /admin/users/{id}, ...)
router.include_router(users.router)
