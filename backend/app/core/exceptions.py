"""
Axiom Design Engine - Custom Exceptions
Application-specific exception classes with HTTP status codes
"""

from typing import Any


class AxiomException(Exception):
    """Base exception for all Axiom-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# Authentication Exceptions
# =============================================================================


class AuthenticationError(AxiomException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            details={"hint": "Check your email and password and try again"},
        )


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(self) -> None:
        super().__init__(
            message="Token has expired",
            details={"hint": "Please log in again to get a new token"},
        )


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid or malformed token",
            details={"hint": "Ensure the token is correct and not corrupted"},
        )


# =============================================================================
# Authorization Exceptions
# =============================================================================


class AuthorizationError(AxiomException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "Permission denied",
        required_role: str | None = None,
    ) -> None:
        details = {}
        if required_role:
            details["required_role"] = required_role
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user doesn't have required role."""

    def __init__(self, required_role: str) -> None:
        super().__init__(
            message=f"This action requires '{required_role}' role",
            required_role=required_role,
        )


# =============================================================================
# Resource Exceptions
# =============================================================================


class NotFoundError(AxiomException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
    ) -> None:
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str | None = None) -> None:
        super().__init__(resource_type="User", resource_id=user_id)


class JobNotFoundError(NotFoundError):
    """Raised when a job is not found."""

    def __init__(self, job_id: str | None = None) -> None:
        super().__init__(resource_type="Job", resource_id=job_id)


class AssetNotFoundError(NotFoundError):
    """Raised when an asset is not found."""

    def __init__(self, asset_id: str | None = None) -> None:
        super().__init__(resource_type="Asset", resource_id=asset_id)


class ProjectNotFoundError(NotFoundError):
    """Raised when a project is not found."""

    def __init__(self, project_id: str | None = None) -> None:
        super().__init__(resource_type="Project", resource_id=project_id)


# =============================================================================
# Validation Exceptions
# =============================================================================


class ValidationError(AxiomException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors or []},
        )


class DuplicateError(AxiomException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(
        self,
        resource_type: str,
        field: str,
        value: str,
    ) -> None:
        super().__init__(
            message=f"{resource_type} with {field} '{value}' already exists",
            status_code=409,
            error_code="DUPLICATE_ERROR",
            details={"resource_type": resource_type, "field": field},
        )


# =============================================================================
# Job Exceptions
# =============================================================================


class JobError(AxiomException):
    """Base exception for job-related errors."""

    def __init__(
        self,
        message: str,
        job_id: str | None = None,
        status_code: int = 400,
        error_code: str = "JOB_ERROR",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details={"job_id": job_id} if job_id else {},
        )


class JobAlreadyExistsError(JobError):
    """Raised when attempting to create a duplicate job."""

    def __init__(self, job_id: str) -> None:
        super().__init__(
            message="Job already exists",
            job_id=job_id,
            status_code=409,
            error_code="JOB_ALREADY_EXISTS",
        )


class JobExecutionError(JobError):
    """Raised when job execution fails."""

    def __init__(self, job_id: str, reason: str) -> None:
        super().__init__(
            message=f"Job execution failed: {reason}",
            job_id=job_id,
            status_code=500,
            error_code="JOB_EXECUTION_ERROR",
        )


class JobTimeoutError(JobError):
    """Raised when a job times out."""

    def __init__(self, job_id: str, timeout_seconds: int) -> None:
        super().__init__(
            message=f"Job timed out after {timeout_seconds} seconds",
            job_id=job_id,
            status_code=408,
            error_code="JOB_TIMEOUT",
        )


# =============================================================================
# Storage Exceptions
# =============================================================================


class StorageError(AxiomException):
    """Raised when storage operations fail."""

    def __init__(
        self,
        message: str = "Storage operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="STORAGE_ERROR",
            details=details,
        )


class FileTooLargeError(AxiomException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size: int, actual_size: int) -> None:
        super().__init__(
            message=f"File size ({actual_size} bytes) exceeds maximum allowed ({max_size} bytes)",
            status_code=413,
            error_code="FILE_TOO_LARGE",
            details={"max_size": max_size, "actual_size": actual_size},
        )


# =============================================================================
# Rate Limiting Exceptions
# =============================================================================


class RateLimitExceededError(AxiomException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )
