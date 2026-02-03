"""
Axiom Design Engine - FastAPI Dependencies
Reusable dependency injection components
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
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
    Implements token bucket algorithm.
    """

    def __init__(
        self,
        requests_per_minute: int = settings.rate_limit_per_minute,
        burst: int = settings.rate_limit_burst,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst = burst

    async def __call__(
        self,
        x_forwarded_for: Annotated[str | None, Header()] = None,
    ) -> None:
        """
        Check rate limit for the current request.
        Uses X-Forwarded-For header or falls back to a default key.

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # In production, implement proper rate limiting with Redis
        # This is a placeholder that always passes
        pass


# Common rate limiter instance
rate_limiter = RateLimiter()
RateLimited = Annotated[None, Depends(rate_limiter)]
