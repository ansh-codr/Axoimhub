"""
Axiom Design Engine - FastAPI Dependencies
Reusable dependency injection components
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.core.security import TokenPayload, verify_token
from app.db.session import async_session_maker
from app.models.user import User, UserRole

# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    Creates a new session for each request and ensures cleanup.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> TokenPayload:
    """
    Extract and validate JWT token from Authorization header.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        TokenPayload: Decoded and validated token payload

    Raises:
        AuthenticationError: If no token provided
        InvalidTokenError: If token is invalid
        TokenExpiredError: If token has expired
    """
    if credentials is None:
        raise AuthenticationError("Authorization header required")

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        # Try to decode to check if expired vs invalid
        from app.core.security import decode_token
        from datetime import datetime, timezone

        decoded = decode_token(token)
        if decoded and decoded.exp < datetime.now(timezone.utc):
            raise TokenExpiredError()
        raise InvalidTokenError()

    return payload


# Type alias for token dependency
CurrentToken = Annotated[TokenPayload, Depends(get_current_token)]


async def get_current_user(
    token: CurrentToken,
    db: DbSession,
) -> User:
    """
    Get the current authenticated user from the database.

    Args:
        token: Validated token payload
        db: Database session

    Returns:
        User: Current user model instance

    Raises:
        AuthenticationError: If user not found or inactive
    """
    from app.models.user import User

    user = await db.get(User, UUID(token.sub))

    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(required_role: UserRole):
    """
    Factory for role-based access control dependency.

    Args:
        required_role: Minimum required role

    Returns:
        Dependency function that validates user role

    Example:
        @router.post("/admin/users")
        async def create_user(
            user: Annotated[User, Depends(require_role(UserRole.ADMIN))]
        ):
            ...
    """

    async def role_checker(user: CurrentUser) -> User:
        # Define role hierarchy
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.ADMIN: 1,
        }

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise AuthorizationError(
                message=f"This action requires {required_role.value} role",
                required_role=required_role.value,
            )

        return user

    return role_checker


# Type aliases for role-based dependencies
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: DbSession,
) -> User | None:
    """
    Get the current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.

    Args:
        credentials: Optional bearer token
        db: Database session

    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        payload = verify_token(credentials.credentials, token_type="access")
        if payload is None:
            return None

        from app.models.user import User

        user = await db.get(User, UUID(payload.sub))
        return user if user and user.is_active else None
    except Exception:
        return None


# Type alias for optional user dependency
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


class RateLimiter:
    """
    Rate limiting dependency using Redis.
    Implements token bucket algorithm with atomic evaluation.
    """

    # Lua script for atomic token bucket evaluation
    LUA_SCRIPT = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])

    local data = redis.call('HMGET', key, 'tokens', 'last_updated')
    local tokens = tonumber(data[1])
    local last_updated = tonumber(data[2])

    if not tokens or not last_updated then
        tokens = capacity
        last_updated = now
    else
        local delta = math.max(0, now - last_updated)
        tokens = math.min(capacity, tokens + (delta * refill_rate))
        last_updated = now
    end

    if tokens >= requested then
        tokens = tokens - requested
        redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
        local ttl = math.ceil(capacity / math.max(refill_rate, 0.001)) * 2 + 60
        redis.call('EXPIRE', key, ttl)
        return 1
    else
        redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
        local ttl = math.ceil(capacity / math.max(refill_rate, 0.001)) * 2 + 60
        redis.call('EXPIRE', key, ttl)
        return 0
    end
    """

    def __init__(
        self,
        requests_per_minute: int = settings.rate_limit_per_minute,
        burst: int = settings.rate_limit_burst,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.refill_rate = requests_per_minute / 60.0

    async def __call__(
        self,
        request: Request,
        x_forwarded_for: Annotated[str | None, Header()] = None,
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        """
        Check rate limit for the current request.
        Keyed by user ID (if authenticated) or client IP.

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        import time
        from app.core.redis import get_redis_client

        # Determine identifier
        identifier: str = "unknown"
        if authorization and authorization.startswith("Bearer "):
            try:
                token = authorization.split(" ")[1]
                payload = verify_token(token)
                identifier = f"user:{payload.sub}"
            except Exception:
                identifier = f"token_hash:{hash(authorization)}"
        
        if identifier == "unknown":
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0].strip()
            elif request.client and request.client.host:
                client_ip = request.client.host
            else:
                client_ip = "127.0.0.1"
            identifier = f"ip:{client_ip}"

        key = f"axiom:ratelimit:{identifier}"

        try:
            client = get_redis_client()
            now = time.time()
            allowed = await client.eval(
                self.LUA_SCRIPT,
                1,
                key,
                self.burst,
                self.refill_rate,
                now,
                1,
            )
            if allowed == 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception as e:
            # If Redis connection fails, fail open and log warning
            from app.core.logging import get_logger
            get_logger(__name__).warning(f"Rate limiter Redis check failed: {e}")


# Common rate limiter instance
rate_limiter = RateLimiter()
RateLimited = Annotated[None, Depends(rate_limiter)]
