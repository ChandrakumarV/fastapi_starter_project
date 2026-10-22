from redis.asyncio import Redis, from_url
from fastapi_starter_project.core.config import settings

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Returns the singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Closes the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
