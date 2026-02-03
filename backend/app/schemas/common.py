"""
Axiom Design Engine - Common Pydantic Schemas
Shared schema components used across the API
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class ErrorDetail(BaseSchema):
    """Error detail for validation errors."""

    loc: list[str | int]
    msg: str
    type: str


class ErrorResponse(BaseSchema):
    """Standardized error response schema."""

    error: str
    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SuccessResponse(BaseSchema):
    """Generic success response."""

    success: bool = True
    message: str = "Operation completed successfully"


class PaginationParams(BaseSchema):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str


class IDResponse(BaseSchema):
    """Response containing just an ID."""

    id: UUID
