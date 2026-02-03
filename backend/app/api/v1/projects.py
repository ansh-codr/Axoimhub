"""
Axiom Design Engine - Project Routes
Project creation and management
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import AuthorizationError, ProjectNotFoundError
from app.models.job import Job
from app.models.project import Project
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.job import JobSummaryResponse
from app.schemas.project import (
    CreateProjectRequest,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectSummaryResponse,
    UpdateProjectRequest,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Create a new project for organizing generation jobs.",
)
async def create_project(
    request: CreateProjectRequest,
    user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    """
    Create a new project.

    - **name**: Project name (required)
    - **description**: Optional project description

    Returns the created project.
    """
    project = Project(
        user_id=user.id,
        name=request.name,
        description=request.description,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        job_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[ProjectSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Projects",
    description="List user's projects with pagination.",
)
async def list_projects(
    user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ProjectSummaryResponse]:
    """
    List user's projects with job counts.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    # Count total projects
    count_query = select(func.count()).where(Project.user_id == user.id)
    total = await db.scalar(count_query) or 0

    # Get projects with job counts
    offset = (page - 1) * page_size

    # Subquery for job count
    job_count_subq = (
        select(Job.project_id, func.count(Job.id).label("job_count"))
        .group_by(Job.project_id)
        .subquery()
    )

    query = (
        select(
            Project,
            func.coalesce(job_count_subq.c.job_count, 0).label("job_count"),
        )
        .outerjoin(job_count_subq, Project.id == job_count_subq.c.project_id)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    items = [
        ProjectSummaryResponse(
            id=row.Project.id,
            name=row.Project.name,
            job_count=row.job_count,
            created_at=row.Project.created_at,
        )
        for row in rows
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Get project details with recent jobs.",
)
async def get_project(
    project_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> ProjectDetailResponse:
    """
    Get project details including recent jobs.

    - **project_id**: UUID of the project
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.jobs))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise ProjectNotFoundError(str(project_id))

    if project.user_id != user.id:
        raise AuthorizationError("You do not have access to this project")

    # Get recent jobs (limit to 10)
    recent_jobs = sorted(project.jobs, key=lambda j: j.created_at, reverse=True)[:10]

    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        job_count=len(project.jobs),
        created_at=project.created_at,
        updated_at=project.updated_at,
        recent_jobs=[
            JobSummaryResponse(
                id=job.id,
                job_type=job.job_type.value,
                status=job.status.value,
                prompt=job.prompt[:100] + "..." if len(job.prompt) > 100 else job.prompt,
                progress=job.progress,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
            for job in recent_jobs
        ],
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project",
    description="Update project name or description.",
)
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    """
    Update project details.

    - **project_id**: UUID of the project
    - **name**: New project name (optional)
    - **description**: New description (optional)
    """
    project = await db.get(Project, project_id)

    if project is None:
        raise ProjectNotFoundError(str(project_id))

    if project.user_id != user.id:
        raise AuthorizationError("You do not have access to this project")

    # Update fields if provided
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description

    await db.commit()
    await db.refresh(project)

    # Get job count
    count_result = await db.execute(
        select(func.count()).where(Job.project_id == project.id)
    )
    job_count = count_result.scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        job_count=job_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete(
    "/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Project",
    description="Delete a project and all its jobs and assets.",
)
async def delete_project(
    project_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> SuccessResponse:
    """
    Delete a project.

    - **project_id**: UUID of the project to delete

    Warning: This will delete all jobs and assets in the project.
    """
    project = await db.get(Project, project_id)

    if project is None:
        raise ProjectNotFoundError(str(project_id))

    if project.user_id != user.id:
        raise AuthorizationError("You do not have access to this project")

    # TODO: Delete all associated files from storage

    await db.delete(project)
    await db.commit()

    return SuccessResponse(message="Project deleted successfully")
