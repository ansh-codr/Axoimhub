"""
Axiom Design Engine - Asset Schemas
Request and response schemas for asset endpoints
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema


class AssetTypeEnum(str, Enum):
    """Asset type enumeration."""

    IMAGE = "image"
    VIDEO = "video"
    MODEL_3D = "model3d"


# =============================================================================
# Response Schemas
# =============================================================================


class AssetResponse(BaseSchema):
    """Full asset response with metadata."""

    id: UUID
    job_id: UUID
    asset_type: AssetTypeEnum
    filename: str
    mime_type: str
    file_size: int = Field(description="File size in bytes")
    width: int | None = Field(default=None, description="Width in pixels")
    height: int | None = Field(default=None, description="Height in pixels")
    duration: float | None = Field(default=None, description="Duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict)
    url: str = Field(description="Signed URL for asset access")
    created_at: datetime


class AssetSummaryResponse(BaseSchema):
    """Abbreviated asset response for lists."""

    id: UUID
    asset_type: AssetTypeEnum
    filename: str
    file_size: int
    thumbnail_url: str | None = None
    created_at: datetime


class AssetDownloadResponse(BaseSchema):
    """Response with download URL."""

    id: UUID
    filename: str
    download_url: str
    expires_in: int = Field(description="URL expiration in seconds")


class AssetUploadResponse(BaseSchema):
    """Response after uploading a reference asset."""

    id: UUID
    asset_type: AssetTypeEnum
    filename: str
    file_size: int
    upload_url: str | None = Field(
        default=None,
        description="Pre-signed upload URL (for multipart uploads)",
    )
