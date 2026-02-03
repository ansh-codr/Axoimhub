"""
Axiom Design Engine - Asset Model
SQLAlchemy model for generated assets (images, videos, 3D models)
"""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job


class AssetType(str, enum.Enum):
    """Type of generated asset."""

    IMAGE = "image"
    VIDEO = "video"
    MODEL_3D = "model3d"


class Asset(Base, UUIDMixin, TimestampMixin):
    """
    Asset model for storing generated content references.

    Attributes:
        id: Unique identifier (UUID)
        job_id: Parent job ID (foreign key)
        asset_type: Type of asset (image/video/3d)
        storage_path: Path in storage backend
        filename: Original/generated filename
        mime_type: MIME type of the asset
        file_size: Size in bytes
        width: Width in pixels (for images/videos)
        height: Height in pixels (for images/videos)
        duration: Duration in seconds (for videos)
        metadata: Additional asset metadata (JSONB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "assets"

    # Job reference
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Asset type
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(
            AssetType,
            name="asset_type",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        index=True,
    )

    # Storage info
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(127),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Dimensions (for images and videos)
    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Duration (for videos)
    duration: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    # Flexible metadata (renamed to avoid SQLAlchemy conflict)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="assets",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, type={self.asset_type}, path={self.storage_path})>"

    @property
    def is_image(self) -> bool:
        """Check if asset is an image."""
        return self.asset_type == AssetType.IMAGE

    @property
    def is_video(self) -> bool:
        """Check if asset is a video."""
        return self.asset_type == AssetType.VIDEO

    @property
    def is_3d_model(self) -> bool:
        """Check if asset is a 3D model."""
        return self.asset_type == AssetType.MODEL_3D
