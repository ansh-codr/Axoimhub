"""
Axiom Design Engine - Project Schemas
Request and response schemas for project endpoints
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.job import JobSummaryResponse


# =============================================================================
# Request Schemas
# =============================================================================


class CreateProjectRequest(BaseSchema):
    """Create a new project."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name",
        examples=["My UI Design Project"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Project description",
    )


class UpdateProjectRequest(BaseSchema):
    """Update an existing project."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New project name",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="New project description",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class ProjectResponse(BaseSchema):
    """Full project response."""

    id: UUID
    name: str
    description: str | None = None
    job_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Project with recent jobs."""

    recent_jobs: list[JobSummaryResponse] = Field(
        default_factory=list,
        description="Most recent jobs in this project",
    )


class ProjectSummaryResponse(BaseSchema):
    """Abbreviated project response for lists."""

    id: UUID
    name: str
    job_count: int = 0
    created_at: datetime
