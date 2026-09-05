"""
Axiom Design Engine - Redis Client Management
Asynchronous Redis connection pool and utilities
"""

from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_pool: Optional[aioredis.ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Get or create singleton async Redis client."""
    global _redis_pool, _redis_client
    if _redis_client is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
        _redis_client = aioredis.Redis(connection_pool=_redis_pool)
    return _redis_client


async def close_redis_client() -> None:
    """Close async Redis client and connection pool."""
    global _redis_pool, _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None


async def check_redis_health() -> bool:
    """Ping Redis to verify connectivity."""
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False
