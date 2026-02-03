"""
Axiom Design Engine - Authentication Routes
Login, registration, token refresh, and password management
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DbSession, RateLimited
from app.core.exceptions import (
    AuthenticationError,
    DuplicateError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_token_pair,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    AuthenticatedUserResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=AuthenticatedUserResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate with email and password to receive JWT tokens.",
)
async def login(
    request: LoginRequest,
    db: DbSession,
    _: RateLimited,
) -> AuthenticatedUserResponse:
    """
    Authenticate user and issue JWT token pair.

    - **email**: User's registered email address
    - **password**: User's password

    Returns access token, refresh token, and user profile.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsError()

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError()

    # Check if account is active
    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # Generate tokens
    token_pair = create_token_pair(user.id, user.role.value)

    return AuthenticatedUserResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
        tokens=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        ),
    )


@router.post(
    "/register",
    response_model=AuthenticatedUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Create a new user account.",
)
async def register(
    request: RegisterRequest,
    db: DbSession,
    _: RateLimited,
) -> AuthenticatedUserResponse:
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **password**: Password (min 8 chars, requires uppercase, lowercase, digit)
    - **password_confirm**: Password confirmation

    Returns access token, refresh token, and user profile.
    """
    email = request.email.lower()

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise DuplicateError(
            resource_type="User",
            field="email",
            value=email,
        )

    # Create new user
    user = User(
        email=email,
        username=request.username,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=UserRole.USER,
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    token_pair = create_token_pair(user.id, user.role.value)

    return AuthenticatedUserResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
        tokens=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Token",
    description="Exchange a refresh token for a new token pair.",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DbSession,
) -> TokenResponse:
    """
    Exchange refresh token for new access and refresh tokens.

    - **refresh_token**: Valid refresh token from login/register

    Returns new access token and refresh token.
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")

    if payload is None:
        raise AuthenticationError("Invalid or expired refresh token")

    # Get user from database
    from uuid import UUID

    user = await db.get(User, UUID(payload.sub))

    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    # Generate new token pair
    token_pair = create_token_pair(user.id, user.role.value)

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get the currently authenticated user's profile.",
)
async def get_current_user_profile(
    user: CurrentUser,
) -> UserResponse:
    """
    Get authenticated user's profile.

    Requires valid access token in Authorization header.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change the current user's password.",
)
async def change_password(
    request: ChangePasswordRequest,
    user: CurrentUser,
    db: DbSession,
) -> SuccessResponse:
    """
    Change authenticated user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars)
    - **new_password_confirm**: New password confirmation
    """
    # Verify current password
    if not verify_password(request.current_password, user.password_hash):
        raise AuthenticationError("Current password is incorrect")

    # Update password
    user.password_hash = hash_password(request.new_password)
    await db.commit()

    return SuccessResponse(message="Password changed successfully")


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Logout the current user (client should discard tokens).",
)
async def logout(
    user: CurrentUser,
) -> SuccessResponse:
    """
    Logout endpoint.

    Note: JWT tokens are stateless, so this endpoint is primarily
    for client-side token cleanup. In production, consider implementing
    a token blacklist using Redis for immediate token invalidation.
    """
    return SuccessResponse(message="Logged out successfully")
