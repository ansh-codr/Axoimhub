"""
Axiom Design Engine - Job Schemas
Request and response schemas for job endpoints
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


class JobTypeEnum(str, Enum):
    """Supported job types."""

    IMAGE = "image"
    VIDEO = "video"
    MODEL_3D = "model3d"


class JobStatusEnum(str, Enum):
    """Job status values."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Request Schemas
# =============================================================================


class ImageGenerationParams(BaseSchema):
    """Parameters specific to image generation."""

    width: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Output image width",
    )
    height: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Output image height",
    )
    num_inference_steps: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of denoising steps",
    )
    guidance_scale: float = Field(
        default=7.5,
        ge=1.0,
        le=20.0,
        description="Classifier-free guidance scale",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    model: str = Field(
        default="sdxl",
        description="Model to use for generation",
    )
    scheduler: str = Field(
        default="euler",
        description="Sampling scheduler",
    )


class VideoGenerationParams(BaseSchema):
    """Parameters specific to video generation."""

    width: int = Field(
        default=1024,
        ge=256,
        le=2048,
        description="Output video width",
    )
    height: int = Field(
        default=576,
        ge=256,
        le=1080,
        description="Output video height",
    )
    num_frames: int = Field(
        default=24,
        ge=8,
        le=720,
        description="Number of frames to generate",
    )
    fps: int = Field(
        default=24,
        ge=8,
        le=60,
        description="Frames per second",
    )
    motion_bucket_id: int = Field(
        default=127,
        ge=1,
        le=255,
        description="Motion intensity",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    model: str = Field(
        default="svd",
        description="Video model to use",
    )


class Model3DGenerationParams(BaseSchema):
    """Parameters specific to 3D model generation."""

    output_format: str = Field(
        default="glb",
        pattern="^(glb|obj|fbx)$",
        description="Output 3D format",
    )
    texture_resolution: int = Field(
        default=1024,
        ge=256,
        le=4096,
        description="Texture resolution",
    )
    poly_count: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
        description="Polygon count level",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )


class CreateJobRequest(BaseSchema):
    """Create a new generation job."""

    project_id: UUID = Field(
        ...,
        description="Project to associate the job with",
    )
    job_type: JobTypeEnum = Field(
        ...,
        description="Type of generation job",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Generation prompt",
    )
    negative_prompt: str | None = Field(
        default=None,
        max_length=1000,
        description="Negative prompt (what to avoid)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Job-specific parameters",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Clean and validate prompt."""
        v = v.strip()
        if not v:
            raise ValueError("Prompt cannot be empty")
        return v


class RetryJobRequest(BaseSchema):
    """Request to retry a failed job."""

    preserve_seed: bool = Field(
        default=True,
        description="Keep the same seed for retry",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class JobResponse(BaseSchema):
    """Job response with full details."""

    id: UUID
    project_id: UUID
    job_type: JobTypeEnum
    status: JobStatusEnum
    prompt: str
    negative_prompt: str | None = None
    parameters: dict[str, Any]
    progress: int = Field(ge=0, le=100)
    error_message: str | None = None
    retry_count: int = 0
    worker_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    result_asset_ids: list[UUID] = Field(default_factory=list)


class JobSummaryResponse(BaseSchema):
    """Abbreviated job response for lists."""

    id: UUID
    job_type: JobTypeEnum
    status: JobStatusEnum
    prompt: str
    progress: int
    created_at: datetime
    completed_at: datetime | None = None


class CreateJobResponse(BaseSchema):
    """Response after creating a job."""

    job_id: UUID
    status: JobStatusEnum = JobStatusEnum.QUEUED
    message: str = "Job queued successfully"


class JobProgressUpdate(BaseSchema):
    """Real-time job progress update (for WebSocket)."""

    job_id: UUID
    status: JobStatusEnum
    progress: int
    message: str | None = None
    preview_url: str | None = None
