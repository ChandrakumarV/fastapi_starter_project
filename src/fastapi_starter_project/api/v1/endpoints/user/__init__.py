"""API v1 endpoint handlers."""
from fastapi import APIRouter
from fastapi_starter_project.api.v1.endpoints.user import auth, me

router = APIRouter()

# Authentication endpoints (/auth/...)
router.include_router(auth.router)

# Profile endpoints (/me)
router.include_router(me.router)
