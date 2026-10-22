from enum import Enum


class UserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_USER = "platform_user"
    TENANT_ADMIN = "tenant_admin"
    TENANT_USER = "tenant_user"
