"""
Axiom Design Engine - Job Service
Core service for managing generation jobs
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_config import Permission
from app.core.authorization import AuthorizationService
from app.core.exceptions import (
    JobNotFoundError,
    ValidationError,
    AuthorizationError,
)
from app.models.job import Job, JobStatus
from app.models.user import User
from app.utils.job_limiter import JobLimiter, ResourceLimiter
from app.utils.prompt_sanitizer import PromptSanitizer


class JobService:
    """
    Service for managing generation jobs.
    
    Handles job creation, status updates, and coordination with workers.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sanitizer = PromptSanitizer()

    # =========================================================================
    # Job Creation
    # =========================================================================

    async def create_job(
        self,
        user: User,
        project_id: UUID,
        job_type: str,
        prompt: str,
        negative_prompt: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Job:
        """
        Create a new generation job.
        
        Args:
            user: User creating the job
            project_id: Project to associate job with
            job_type: Type of job (image, video, model3d)
            prompt: Generation prompt
            negative_prompt: Optional negative prompt
            parameters: Job-specific parameters
            
        Returns:
            Created Job instance
            
        Raises:
            ValidationError: If job creation fails validation
            AuthorizationError: If user lacks permission
        """
        # Check permissions
        AuthorizationService.require_permission_or_raise(
            user, Permission.CREATE_JOB
        )

        # Enforce rate limits
        allowed, reason = await JobLimiter.enforce_job_limits(user.id, self.db)
        if not allowed:
            raise ValidationError(reason)

        # Sanitize prompt
        clean_prompt = self.sanitizer.sanitize(prompt)
        clean_negative = (
            self.sanitizer.sanitize(negative_prompt) if negative_prompt else None
        )

        # Validate parameters based on job type
        parameters = parameters or {}
        await self._validate_job_parameters(job_type, parameters)

        # Create job
        job = Job(
            user_id=user.id,
            project_id=project_id,
            job_type=job_type,
            prompt=clean_prompt,
            negative_prompt=clean_negative,
            parameters=parameters,
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Dispatch to worker queue
        await self._dispatch_job(job)

        return job

    async def _validate_job_parameters(
        self, job_type: str, parameters: dict[str, Any]
    ) -> None:
        """Validate job parameters based on type."""
        if job_type == "image":
            width = parameters.get("width", 1024)
            height = parameters.get("height", 1024)
            ResourceLimiter.validate_image_resolution(width, height)

        elif job_type == "video":
            frames = parameters.get("num_frames", parameters.get("frames", 24))
            fps = parameters.get("fps", 8)
            duration = parameters.get("duration_seconds")
            if duration is None:
                try:
                    duration = int(frames) / int(fps)
                except (TypeError, ValueError, ZeroDivisionError):
                    duration = 3

            ResourceLimiter.validate_video_duration(duration)
            ResourceLimiter.validate_video_frames(frames, fps)

        elif job_type == "model3d":
            # 3D validation will happen during generation
            pass

    async def _dispatch_job(self, job: Job) -> str:
        """Dispatch job to worker queue."""
        # Import here to avoid circular dependency
        from workers.dispatcher import JobDispatcher

        task_id = JobDispatcher.dispatch(
            job_id=str(job.id),
            job_type=job.job_type,
            user_id=str(job.user_id),
            project_id=str(job.project_id),
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            parameters=job.parameters,
        )

        # Update job with task ID
        job.task_id = task_id
        job.status = JobStatus.QUEUED
        await self.db.commit()

        return task_id

    # =========================================================================
    # Job Retrieval
    # =========================================================================

    async def get_job(self, job_id: UUID, user: User) -> Job:
        """
        Get a job by ID.
        
        Args:
            job_id: Job identifier
            user: User requesting the job
            
        Returns:
            Job instance
            
        Raises:
            JobNotFoundError: If job doesn't exist
            AuthorizationError: If user can't access job
        """
        job = await self.db.get(Job, job_id)
        
        if job is None:
            raise JobNotFoundError(str(job_id))

        # Check access
        if not AuthorizationService.user_can_access_job(user, job.user_id):
            raise AuthorizationError("You don't have access to this job")

        return job

    async def list_jobs(
        self,
        user: User,
        project_id: UUID | None = None,
        job_type: str | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """
        List jobs with optional filters.
        
        Args:
            user: User requesting jobs
            project_id: Optional project filter
            job_type: Optional type filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Job instances
        """
        # Build query
        conditions = []

        # Users see only their jobs, admins see all
        if not user.is_admin:
            conditions.append(Job.user_id == user.id)

        if project_id:
            conditions.append(Job.project_id == project_id)
        if job_type:
            conditions.append(Job.job_type == job_type)
        if status:
            conditions.append(Job.status == status)

        query = (
            select(Job)
            .where(and_(*conditions) if conditions else True)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Job Status Management
    # =========================================================================

    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: int | None = None,
        error_message: str | None = None,
    ) -> Job:
        """
        Update job status (used by worker callbacks).
        
        Args:
            job_id: Job identifier
            status: New status
            progress: Optional progress percentage
            error_message: Optional error message
            
        Returns:
            Updated Job instance
        """
        job = await self.db.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(str(job_id))

        job.status = status
        
        if progress is not None:
            job.progress = progress

        if error_message:
            job.error_message = error_message

        # Track timing
        if status == JobStatus.RUNNING and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def cancel_job(self, job_id: UUID, user: User) -> Job:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
            user: User requesting cancellation
            
        Returns:
            Updated Job instance
        """
        job = await self.get_job(job_id, user)

        # Check if cancellable
        if job.status not in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING):
            raise ValidationError(f"Cannot cancel job in {job.status.value} status")

        # Request worker to cancel
        if job.task_id:
            from workers.celery_app import celery_app
            celery_app.control.revoke(job.task_id, terminate=True)

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

        return job

    async def retry_job(self, job_id: UUID, user: User) -> Job:
        """
        Retry a failed job.
        
        Args:
            job_id: Job identifier
            user: User requesting retry
            
        Returns:
            New Job instance (clone of original)
        """
        original = await self.get_job(job_id, user)

        # Only failed or cancelled jobs can be retried
        if original.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
            raise ValidationError(f"Cannot retry job in {original.status.value} status")

        # Create new job with same parameters
        return await self.create_job(
            user=user,
            project_id=original.project_id,
            job_type=original.job_type,
            prompt=original.prompt,
            negative_prompt=original.negative_prompt,
            parameters=original.parameters,
        )

    # =========================================================================
    # Job Completion
    # =========================================================================

    async def complete_job(
        self,
        job_id: UUID,
        asset_id: UUID,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """
        Mark job as complete with generated asset.
        
        Args:
            job_id: Job identifier
            asset_id: Generated asset ID
            metadata: Optional generation metadata
            
        Returns:
            Updated Job instance
        """
        job = await self.db.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(str(job_id))

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.result_asset_id = asset_id
        job.completed_at = datetime.now(timezone.utc)
        
        if metadata:
            job.metadata = {**(job.metadata or {}), **metadata}

        await self.db.commit()
        await self.db.refresh(job)

        return job
