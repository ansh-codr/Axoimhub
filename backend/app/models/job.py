"""
Axiom Design Engine - Job Model
SQLAlchemy model for AI generation jobs with lifecycle tracking
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.project import Project


class JobType(str, enum.Enum):
    """Type of AI generation job."""

    IMAGE = "image"
    VIDEO = "video"
    MODEL_3D = "model3d"


class JobStatus(str, enum.Enum):
    """Job lifecycle status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base, UUIDMixin, TimestampMixin):
    """
    Job model for tracking AI generation tasks.

    Attributes:
        id: Unique identifier (UUID)
        project_id: Parent project ID (foreign key)
        job_type: Type of generation (image/video/3d)
        status: Current job status
        prompt: User's generation prompt
        negative_prompt: Optional negative prompt
        parameters: Job-specific parameters (JSONB)
        progress: Progress percentage (0-100)
        error_message: Error details if failed
        retry_count: Number of retry attempts
        worker_id: ID of processing worker
        started_at: When job started processing
        completed_at: When job finished
        created_at: Job creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "jobs"

    # Project reference
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Job type and status
    job_type: Mapped[JobType] = mapped_column(
        Enum(
            JobType,
            name="job_type",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )

    # Generation inputs
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    negative_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Progress tracking
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Worker tracking
    worker_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="jobs",
        lazy="joined",
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (completed or failed)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        from app.core.config import settings

        return (
            self.status == JobStatus.FAILED
            and self.retry_count < settings.job_max_retries
        )
