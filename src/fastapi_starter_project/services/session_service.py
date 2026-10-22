import json
from datetime import datetime, timezone
from typing import Any
import uuid
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.redis import get_redis


class SessionService:
    """Manages Redis-backed sessions for tenant users and tenant administrators."""

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def _user_sessions_key(user_id: str) -> str:
        return f"user_sessions:{user_id}"

    @staticmethod
    def _tenant_sessions_key(tenant_id: str) -> str:
        return f"tenant_sessions:{tenant_id}"

    async def create_session(
        self,
        user_id: str | uuid.UUID,
        tenant_id: str | uuid.UUID | None = None,
        role: str = "",
        extra_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Creates a new session in Redis, indexable by user_id and tenant_id.
        Accepts flexible positional arguments (e.g. user_id, role, tenant_id or user_id, tenant_id, role).
        Returns the generated session_id.
        """
        # Auto-detect if caller passed role as second argument (e.g. create_session(user_id, "tenant_user", tenant_id))
        if isinstance(tenant_id, str) and not role:
            if tenant_id in (
                "platform_admin", "platform_user", "tenant_admin", "tenant_user"
            ):
                role = tenant_id
                tenant_id = None
        elif isinstance(tenant_id, str) and role and isinstance(role, (uuid.UUID, str)):
            # If tenant_id was passed a role string and role was passed a tenant_id
            if tenant_id in (
                "platform_admin", "platform_user", "tenant_admin", "tenant_user"
            ):
                actual_role = tenant_id
                actual_tenant_id = role
                role = actual_role
                tenant_id = actual_tenant_id

        session_id = str(uuid.uuid4())
        u_id = str(user_id)
        t_id = str(tenant_id) if tenant_id else ""

        session_payload = {
            "session_id": session_id,
            "user_id": u_id,
            "tenant_id": t_id,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra_data:
            session_payload.update(extra_data)

        redis = get_redis()
        ttl = settings.SESSION_EXPIRE_SECONDS

        # 1. Store session payload
        await redis.set(
            self._session_key(session_id),
            json.dumps(session_payload, default=str),
            ex=ttl,
        )

        # 2. Add to user index
        await redis.sadd(self._user_sessions_key(u_id), session_id)
        await redis.expire(self._user_sessions_key(u_id), ttl)

        # 3. Add to tenant index if tenant_id is provided
        if t_id:
            await redis.sadd(self._tenant_sessions_key(t_id), session_id)
            await redis.expire(self._tenant_sessions_key(t_id), ttl)

        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieves an active session payload from Redis if valid and unexpired."""
        redis = get_redis()
        data = await redis.get(self._session_key(session_id))
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            return None

    async def is_session_valid(self, session_id: str) -> bool:
        """Checks if a session is currently active in Redis."""
        redis = get_redis()
        return bool(await redis.exists(self._session_key(session_id)))

    async def invalidate_session(self, session_id: str) -> None:
        """Invalidates a single session and removes it from index sets."""
        redis = get_redis()
        data = await self.get_session(session_id)
        if data:
            u_id = data.get("user_id")
            t_id = data.get("tenant_id")
            if u_id:
                await redis.srem(self._user_sessions_key(u_id), session_id)
            if t_id:
                await redis.srem(self._tenant_sessions_key(t_id), session_id)
        await redis.delete(self._session_key(session_id))

    async def invalidate_user_sessions(self, user_id: str | uuid.UUID) -> None:
        """Invalidates all active sessions for a given user."""
        redis = get_redis()
        u_key = self._user_sessions_key(str(user_id))
        session_ids = await redis.smembers(u_key)
        if session_ids:
            keys_to_del = [self._session_key(sid) for sid in session_ids]
            await redis.delete(*keys_to_del)
        await redis.delete(u_key)

    async def invalidate_tenant_sessions(self, tenant_id: str | uuid.UUID) -> None:
        """Invalidates all active sessions for all users belonging to a tenant."""
        redis = get_redis()
        t_key = self._tenant_sessions_key(str(tenant_id))
        session_ids = await redis.smembers(t_key)
        if session_ids:
            keys_to_del = [self._session_key(sid) for sid in session_ids]
            await redis.delete(*keys_to_del)
        await redis.delete(t_key)


session_service = SessionService()
