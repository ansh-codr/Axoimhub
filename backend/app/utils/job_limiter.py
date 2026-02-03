"""
Axiom Design Engine - Job Limits and Rate Limiting
Enforce rate limits and resource constraints per user
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_config import JOB_LIMITS, RESOURCE_LIMITS
from app.core.exceptions import ValidationError
from app.models.job import Job, JobStatus


class JobLimiter:
    """Enforce job creation limits and rate limits."""

    @staticmethod
    async def check_concurrent_jobs(user_id: UUID, db: AsyncSession) -> bool:
        """
        Check if user has exceeded concurrent job limit.

        Args:
            user_id: User's unique identifier
            db: Database session

        Returns:
            True if under limit, False otherwise
        """
        max_concurrent = JOB_LIMITS.get("max_concurrent_jobs_per_user", 3)

        # Count jobs that are in progress (not completed/failed/cancelled)
        result = await db.execute(
            select(func.count(Job.id)).where(
                and_(
                    Job.user_id == user_id,
                    Job.status.in_(
                        [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]
                    ),
                )
            )
        )
        current_concurrent = result.scalar() or 0

        return current_concurrent < max_concurrent

    @staticmethod
    async def check_daily_job_limit(user_id: UUID, db: AsyncSession) -> bool:
        """
        Check if user has exceeded daily job limit.

        Args:
            user_id: User's unique identifier
            db: Database session

        Returns:
            True if under limit, False otherwise
        """
        max_daily = JOB_LIMITS.get("max_jobs_per_day", 100)

        # Count jobs created in the last 24 hours
        since = datetime.now(timezone.utc) - timedelta(days=1)

        result = await db.execute(
            select(func.count(Job.id)).where(
                and_(
                    Job.user_id == user_id,
                    Job.created_at >= since,
                )
            )
        )
        daily_count = result.scalar() or 0

        return daily_count < max_daily

    @staticmethod
    async def check_hourly_job_limit(user_id: UUID, db: AsyncSession) -> bool:
        """
        Check if user has exceeded hourly job limit.

        Args:
            user_id: User's unique identifier
            db: Database session

        Returns:
            True if under limit, False otherwise
        """
        max_hourly = JOB_LIMITS.get("max_jobs_per_hour", 20)

        # Count jobs created in the last hour
        since = datetime.now(timezone.utc) - timedelta(hours=1)

        result = await db.execute(
            select(func.count(Job.id)).where(
                and_(
                    Job.user_id == user_id,
                    Job.created_at >= since,
                )
            )
        )
        hourly_count = result.scalar() or 0

        return hourly_count < max_hourly

    @classmethod
    async def enforce_job_limits(
        cls, user_id: UUID, db: AsyncSession
    ) -> tuple[bool, str]:
        """
        Enforce all job creation limits.

        Args:
            user_id: User's unique identifier
            db: Database session

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check concurrent limit
        if not await cls.check_concurrent_jobs(user_id, db):
            max_concurrent = JOB_LIMITS.get("max_concurrent_jobs_per_user", 3)
            return (
                False,
                f"Maximum {max_concurrent} concurrent jobs allowed. Please wait for current jobs to complete.",
            )

        # Check daily limit
        if not await cls.check_daily_job_limit(user_id, db):
            max_daily = JOB_LIMITS.get("max_jobs_per_day", 100)
            return (False, f"Daily job limit of {max_daily} exceeded")

        # Check hourly limit
        if not await cls.check_hourly_job_limit(user_id, db):
            max_hourly = JOB_LIMITS.get("max_jobs_per_hour", 20)
            return (False, f"Hourly job limit of {max_hourly} exceeded")

        return (True, "")


class ResourceLimiter:
    """Validate resource requirements for generation jobs."""

    @staticmethod
    def validate_image_resolution(width: int, height: int) -> bool:
        """
        Validate image resolution limits.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            True if valid, raises ValidationError otherwise
        """
        limits = RESOURCE_LIMITS["max_image_resolution"]

        if width > limits["width"] or height > limits["height"]:
            raise ValidationError(
                f"Image resolution must not exceed {limits['width']}x{limits['height']} pixels"
            )

        # Check megapixel limit
        megapixels = (width * height) / 1_000_000
        if megapixels > limits["megapixels"]:
            raise ValidationError(
                f"Image megapixels must not exceed {limits['megapixels']:.2f}MP"
            )

        return True

    @staticmethod
    def validate_video_duration(duration_seconds: int) -> bool:
        """
        Validate video duration limits.

        Args:
            duration_seconds: Video duration in seconds

        Returns:
            True if valid, raises ValidationError otherwise
        """
        max_duration = RESOURCE_LIMITS["max_video_duration_seconds"]

        if duration_seconds > max_duration:
            raise ValidationError(
                f"Video duration must not exceed {max_duration} seconds"
            )

        return True

    @staticmethod
    def validate_video_frames(frames: int, fps: int) -> bool:
        """
        Validate video frame count and fps.

        Args:
            frames: Number of frames
            fps: Frames per second

        Returns:
            True if valid, raises ValidationError otherwise
        """
        max_frames = RESOURCE_LIMITS["max_video_frames"]
        max_fps = RESOURCE_LIMITS["max_video_fps"]

        if frames > max_frames:
            raise ValidationError(
                f"Frame count must not exceed {max_frames} frames"
            )

        if fps > max_fps:
            raise ValidationError(f"FPS must not exceed {max_fps} fps")

        # Verify duration
        duration = frames / fps
        ResourceLimiter.validate_video_duration(int(duration))

        return True

    @staticmethod
    def validate_model3d_faces(face_count: int) -> bool:
        """
        Validate 3D model face/polygon limit.

        Args:
            face_count: Number of faces/polygons

        Returns:
            True if valid, raises ValidationError otherwise
        """
        max_faces = RESOURCE_LIMITS["max_3d_mesh_faces"]

        if face_count > max_faces:
            raise ValidationError(
                f"3D model polygon count must not exceed {max_faces:,} faces"
            )

        return True

    @staticmethod
    def validate_file_size(size_bytes: int) -> bool:
        """
        Validate file size limits.

        Args:
            size_bytes: File size in bytes

        Returns:
            True if valid, raises ValidationError otherwise
        """
        max_size_mb = RESOURCE_LIMITS["max_file_size_mb"]
        max_size_bytes = max_size_mb * 1024 * 1024

        if size_bytes > max_size_bytes:
            raise ValidationError(
                f"File size must not exceed {max_size_mb}MB"
            )

        return True
