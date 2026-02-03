"""
Axiom Design Engine - Job Routes
Job creation, status tracking, and management
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import JobNotFoundError, ProjectNotFoundError, AuthorizationError
from app.models.asset import Asset
from app.models.job import Job, JobStatus, JobType
from app.models.project import Project
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.job import (
    CreateJobRequest,
    CreateJobResponse,
    JobResponse,
    JobStatusEnum,
    JobSummaryResponse,
    RetryJobRequest,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def map_job_to_response(job: Job) -> JobResponse:
    """Convert Job model to JobResponse schema."""
    return JobResponse(
        id=job.id,
        project_id=job.project_id,
        job_type=job.job_type.value,
        status=job.status.value,
        prompt=job.prompt,
        negative_prompt=job.negative_prompt,
        parameters=job.parameters,
        progress=job.progress,
        error_message=job.error_message,
        retry_count=job.retry_count,
        worker_id=job.worker_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        result_asset_ids=[asset.id for asset in job.assets],
    )


@router.post(
    "",
    response_model=CreateJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Generation Job",
    description="Submit a new AI generation job (image, video, or 3D model).",
)
async def create_job(
    request: CreateJobRequest,
    user: CurrentUser,
    db: DbSession,
) -> CreateJobResponse:
    """
    Create a new generation job.

    - **project_id**: Project to associate the job with
    - **job_type**: Type of generation (image, video, model3d)
    - **prompt**: Text prompt for generation
    - **negative_prompt**: Optional negative prompt
    - **parameters**: Job-specific parameters (dimensions, steps, etc.)
    - **template_id**: Optional template ID to use for generation

    Returns job ID and initial queued status.
    """
    from app.services import JobService
    
    # Create job service instance
    job_service = JobService(db)
    
    # Create and dispatch job
    job = await job_service.create_job(
        user_id=user.id,
        project_id=request.project_id,
        job_type=request.job_type.value,
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        parameters=request.parameters,
    )

    return CreateJobResponse(
        job_id=job.id,
        status=JobStatusEnum.QUEUED,
        message="Job queued successfully",
    )


@router.get(
    "",
    response_model=PaginatedResponse[JobSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Jobs",
    description="List jobs with optional filtering and pagination.",
)
async def list_jobs(
    user: CurrentUser,
    db: DbSession,
    project_id: Annotated[UUID | None, Query(description="Filter by project")] = None,
    status_filter: Annotated[
        JobStatusEnum | None, Query(alias="status", description="Filter by status")
    ] = None,
    job_type: Annotated[
        str | None, Query(description="Filter by job type")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[JobSummaryResponse]:
    """
    List jobs with filtering and pagination.

    - **project_id**: Filter by specific project
    - **status**: Filter by job status (queued, running, completed, failed)
    - **job_type**: Filter by type (image, video, model3d)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    # Base query - only user's jobs
    query = (
        select(Job)
        .join(Project)
        .where(Project.user_id == user.id)
    )

    # Apply filters
    if project_id:
        query = query.where(Job.project_id == project_id)

    if status_filter:
        status_map = {
            "queued": JobStatus.QUEUED,
            "running": JobStatus.RUNNING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
        }
        query = query.where(Job.status == status_map[status_filter.value])

    if job_type:
        type_map = {
            "image": JobType.IMAGE,
            "video": JobType.VIDEO,
            "model3d": JobType.MODEL_3D,
        }
        if job_type in type_map:
            query = query.where(Job.job_type == type_map[job_type])

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Convert to response
    items = [
        JobSummaryResponse(
            id=job.id,
            job_type=job.job_type.value,
            status=job.status.value,
            prompt=job.prompt[:100] + "..." if len(job.prompt) > 100 else job.prompt,
            progress=job.progress,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Job Details",
    description="Get detailed information about a specific job.",
)
async def get_job(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> JobResponse:
    """
    Get job details including status, progress, and result assets.

    - **job_id**: UUID of the job to retrieve

    Returns full job details with associated asset IDs.
    """
    # Get job with assets
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.assets), selectinload(Job.project))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise JobNotFoundError(str(job_id))

    # Verify ownership
    if job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this job")

    return map_job_to_response(job)


@router.post(
    "/{job_id}/cancel",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Job",
    description="Cancel a queued or running job.",
)
async def cancel_job(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> SuccessResponse:
    """
    Cancel a job if it's still queued or running.

    - **job_id**: UUID of the job to cancel
    """
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.project))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise JobNotFoundError(str(job_id))

    if job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this job")

    if job.is_terminal:
        return SuccessResponse(
            success=False,
            message=f"Job is already {job.status.value} and cannot be cancelled",
        )

    # Update status
    job.status = JobStatus.FAILED
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()

    # TODO: Send cancellation signal to worker if running

    return SuccessResponse(message="Job cancelled successfully")


@router.post(
    "/{job_id}/retry",
    response_model=CreateJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Retry Failed Job",
    description="Retry a failed job with the same parameters.",
)
async def retry_job(
    job_id: UUID,
    request: RetryJobRequest,
    user: CurrentUser,
    db: DbSession,
) -> CreateJobResponse:
    """
    Retry a failed job.

    - **job_id**: UUID of the failed job to retry
    - **preserve_seed**: Keep the same random seed (default: true)
    """
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.project))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise JobNotFoundError(str(job_id))

    if job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this job")

    if not job.can_retry:
        from app.core.config import settings
        return CreateJobResponse(
            job_id=job.id,
            status=JobStatusEnum(job.status.value),
            message=f"Job cannot be retried. Max retries ({settings.job_max_retries}) reached or job not failed.",
        )

    # Create new job based on failed one
    parameters = job.parameters.copy()
    if not request.preserve_seed and "seed" in parameters:
        del parameters["seed"]

    new_job = Job(
        project_id=job.project_id,
        job_type=job.job_type,
        status=JobStatus.QUEUED,
        prompt=job.prompt,
        negative_prompt=job.negative_prompt,
        parameters=parameters,
        progress=0,
        retry_count=job.retry_count + 1,
    )

    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # TODO: Dispatch to worker queue

    return CreateJobResponse(
        job_id=new_job.id,
        status=JobStatusEnum.QUEUED,
        message=f"Job retry #{new_job.retry_count} queued successfully",
    )
