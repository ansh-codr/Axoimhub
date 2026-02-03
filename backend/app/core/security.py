"""
Axiom Design Engine - Security Module
JWT token handling, password hashing, and validation
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.auth_config import PASSWORD_POLICY, TOKEN_CONFIG
from app.core.config import settings

# Password hashing context
# Use bcrypt_sha256 to avoid bcrypt 72-byte limit issues and backend incompatibilities.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto",
    bcrypt_sha256__rounds=settings.password_hash_rounds,
)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user_id)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    type: str  # Token type: "access" or "refresh"
    role: str  # User role


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.

    Args:
        password: Plain text password to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    policy = PASSWORD_POLICY

    # Check length
    if len(password) < policy["min_length"]:
        return (
            False,
            f"Password must be at least {policy['min_length']} characters",
        )

    if len(password) > policy["max_length"]:
        return (
            False,
            f"Password must not exceed {policy['max_length']} characters",
        )

    # Check uppercase
    if policy["require_uppercase"] and not re.search(r"[A-Z]", password):
        return (False, "Password must contain at least one uppercase letter")

    # Check lowercase
    if policy["require_lowercase"] and not re.search(r"[a-z]", password):
        return (False, "Password must contain at least one lowercase letter")

    # Check digits
    if policy["require_digits"] and not re.search(r"\d", password):
        return (False, "Password must contain at least one digit")

    # Check special characters
    if policy["require_special_chars"]:
        special_chars_pattern = re.escape(policy["special_chars"])
        if not re.search(f"[{special_chars_pattern}]", password):
            return (
                False,
                f"Password must contain at least one special character: {policy['special_chars']}",
            )

    return (True, "")


def check_password_strength(password: str) -> None:
    """
    Validate password strength and raise exception if invalid.

    Args:
        password: Plain text password

    Raises:
        ValueError: If password doesn't meet requirements
    """
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        raise ValueError(message)



def create_access_token(
    user_id: UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's unique identifier
        role: User's role (user, admin)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
        "role": role,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    user_id: UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User's unique identifier
        role: User's role
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "role": role,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_pair(user_id: UUID, role: str) -> TokenPair:
    """
    Create both access and refresh tokens.

    Args:
        user_id: User's unique identifier
        role: User's role

    Returns:
        TokenPair with access_token, refresh_token, and metadata
    """
    access_token = create_access_token(user_id, role)
    refresh_token = create_refresh_token(user_id, role)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenPayload | None:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload["type"],
            role=payload["role"],
        )
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> TokenPayload | None:
    """
    Verify a JWT token and check its type.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload if valid and correct type, None otherwise
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.type != token_type:
        return None

    # Check if token is expired
    if payload.exp < datetime.now(timezone.utc):
        return None

    return payload
