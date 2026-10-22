from fastapi import APIRouter
from . import (
    auth,
    me,
    tenant_users,
    tenants,
    users,
)

router = APIRouter(prefix="/platform")

# Authentication endpoints (/platform/login, /platform/logout)
router.include_router(auth.router)

# Profile endpoints (/platform/me)
router.include_router(me.router)

# Tenant Management endpoints (/platform/tenants, /platform/tenants/{tenant_id})
router.include_router(tenants.router)

# Tenant User Management endpoints (/platform/tenants/{tenant_id}/users/...)
router.include_router(tenant_users.router)

# General platform user management (/platform/users, /platform/users/{id}, ...)
router.include_router(users.router)
