"""
Axiom Design Engine - Authentication Schemas
Request and response schemas for auth endpoints
"""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.auth_config import PASSWORD_POLICY
from app.schemas.common import BaseSchema


# =============================================================================
# Request Schemas
# =============================================================================


class LoginRequest(BaseSchema):
    """Login request with email and password."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password",
        examples=["SecureP@ssw0rd!"],
    )


class RegisterRequest(BaseSchema):
    """User registration request."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique username",
        examples=["johndoe"],
    )
    full_name: str | None = Field(
        default=None,
        description="Optional full name",
        examples=["John Doe"],
    )
    password: str = Field(
        ...,
        min_length=PASSWORD_POLICY["min_length"],
        max_length=PASSWORD_POLICY["max_length"],
        description=f"Password (min {PASSWORD_POLICY['min_length']} characters, requires uppercase, lowercase, digit, and special character)",
    )
    password_confirm: str = Field(
        ...,
        description="Password confirmation",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        from app.core.security import check_password_strength

        check_password_strength(v)
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
    )


class ChangePasswordRequest(BaseSchema):
    """Change password request."""

    current_password: str = Field(
        ...,
        description="Current password",
    )
    new_password: str = Field(
        ...,
        min_length=PASSWORD_POLICY["min_length"],
        max_length=PASSWORD_POLICY["max_length"],
        description=f"New password (min {PASSWORD_POLICY['min_length']} characters)",
    )
    new_password_confirm: str = Field(
        ...,
        description="New password confirmation",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password meets security requirements."""
        from app.core.security import check_password_strength

        check_password_strength(v)
        return v

    @field_validator("new_password_confirm")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate new passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v


# =============================================================================
# Response Schemas
# =============================================================================


class TokenResponse(BaseSchema):
    """JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )


class UserResponse(BaseSchema):
    """User profile response."""

    id: UUID
    email: str
    username: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None


class AuthenticatedUserResponse(BaseSchema):
    """Response after successful authentication."""

    user: UserResponse
    tokens: TokenResponse
