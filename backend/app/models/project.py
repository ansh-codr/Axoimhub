"""
Axiom Design Engine - Project Model
SQLAlchemy model for user projects containing jobs
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Project(Base, UUIDMixin, TimestampMixin):
    """
    Project model for organizing user's generation jobs.

    Attributes:
        id: Unique identifier (UUID)
        user_id: Owner's user ID (foreign key)
        name: Project name
        description: Optional project description
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "projects"

    # Owner reference
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Project info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        lazy="joined",
    )
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Job.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, user_id={self.user_id})>"
