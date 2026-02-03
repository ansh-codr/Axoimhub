"""
Axiom Design Engine - Internal API Routes
Routes for worker callbacks and internal services
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import DbSession
from app.models.job import Job, JobStatus
from app.models.asset import Asset, AssetType

router = APIRouter(prefix="/internal", tags=["internal"])


def verify_worker_key(x_worker_key: str = Header(...)) -> None:
    """Verify the worker API key."""
    if x_worker_key != settings.worker_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid worker key",
        )


# =============================================================================
# Request/Response Schemas
# =============================================================================

class JobStatusUpdate(BaseModel):
    """Job status update from worker."""
    
    status: str = Field(..., description="New job status")
    progress: int | None = Field(None, ge=0, le=100, description="Progress percentage")
    error_message: str | None = Field(None, max_length=1000, description="Error message if failed")
    worker_id: str | None = Field(None, description="Worker hostname")


class AssetRegistration(BaseModel):
    """Asset registration from worker."""
    
    job_id: str = Field(..., description="Parent job ID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_type: str = Field(..., description="Asset type (image, video, model3d)")
    storage_path: str = Field(..., description="Storage path")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    width: int | None = Field(None, ge=1, description="Width in pixels")
    height: int | None = Field(None, ge=1, description="Height in pixels")
    duration: float | None = Field(None, ge=0, description="Duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CloudCallbackRequest(BaseModel):
    """Callback from cloud worker execution."""
    
    job_id: str = Field(..., description="Job ID")
    provider: str = Field(..., description="Cloud provider name")
    status: str = Field(..., description="Execution status")
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    execution_time: float | None = None


# =============================================================================
# Routes
# =============================================================================

@router.patch(
    "/jobs/{job_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_worker_key)],
)
async def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    db: AsyncSession = Depends(DbSession),
) -> dict[str, str]:
    """
    Update job status from worker.
    
    Called by workers to report status changes during execution.
    """
    # Find job
    result = await db.execute(
        select(Job).where(Job.id == UUID(job_id))
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Map status string to enum
    status_map = {
        "queued": JobStatus.QUEUED,
        "running": JobStatus.RUNNING,
        "completed": JobStatus.COMPLETED,
        "failed": JobStatus.FAILED,
        "cancelled": JobStatus.CANCELLED,
    }
    
    new_status = status_map.get(update.status.lower())
    if new_status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {update.status}",
        )

    # Update job
    job.status = new_status
    
    if update.progress is not None:
        job.progress = update.progress
    
    if update.error_message:
        job.error_message = update.error_message
    
    if update.worker_id:
        job.worker_id = update.worker_id

    # Set timestamps
    if new_status == JobStatus.RUNNING and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    elif new_status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        job.completed_at = datetime.now(timezone.utc)

    await db.commit()
    
    return {"status": "updated", "job_id": job_id}


@router.post(
    "/assets",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_worker_key)],
)
async def register_asset(
    asset_data: AssetRegistration,
    db: AsyncSession = Depends(DbSession),
) -> dict[str, str]:
    """
    Register a generated asset.
    
    Called by workers after storing artifacts to create database records.
    """
    # Find job
    result = await db.execute(
        select(Job).where(Job.id == UUID(asset_data.job_id))
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Map asset type
    type_map = {
        "image": AssetType.IMAGE,
        "video": AssetType.VIDEO,
        "model3d": AssetType.MODEL_3D,
    }
    
    asset_type = type_map.get(asset_data.asset_type.lower())
    if asset_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset type: {asset_data.asset_type}",
        )

    # Create asset
    asset = Asset(
        id=UUID(asset_data.asset_id),
        job_id=job.id,
        asset_type=asset_type,
        storage_path=asset_data.storage_path,
        filename=asset_data.filename,
        mime_type=asset_data.mime_type,
        file_size=asset_data.file_size,
        width=asset_data.width,
        height=asset_data.height,
        duration=asset_data.duration,
        metadata=asset_data.metadata,
    )

    db.add(asset)
    await db.commit()
    
    return {"status": "created", "asset_id": asset_data.asset_id}


@router.post(
    "/cloud-callback",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_worker_key)],
)
async def cloud_execution_callback(
    callback: CloudCallbackRequest,
    db: AsyncSession = Depends(DbSession),
) -> dict[str, str]:
    """
    Callback endpoint for cloud worker execution.
    
    Called by cloud workers after completing execution to report results.
    """
    # Find job
    result = await db.execute(
        select(Job).where(Job.id == UUID(callback.job_id))
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Update status based on callback
    if callback.status == "completed":
        job.status = JobStatus.COMPLETED
        job.progress = 100
    elif callback.status == "failed":
        job.status = JobStatus.FAILED
        job.error_message = callback.error_message
    
    job.completed_at = datetime.now(timezone.utc)
    
    # Store cloud execution metadata
    if job.metadata is None:
        job.metadata = {}
    job.metadata["cloud_provider"] = callback.provider
    job.metadata["cloud_execution_time"] = callback.execution_time

    # Register artifacts
    for artifact in callback.artifacts:
        asset_type_str = artifact.get("asset_type", "image")
        type_map = {
            "image": AssetType.IMAGE,
            "video": AssetType.VIDEO,
            "model3d": AssetType.MODEL_3D,
        }
        
        asset = Asset(
            id=UUID(artifact.get("asset_id")),
            job_id=job.id,
            asset_type=type_map.get(asset_type_str, AssetType.IMAGE),
            storage_path=artifact.get("storage_path", ""),
            filename=artifact.get("filename", "output"),
            mime_type=artifact.get("mime_type", "application/octet-stream"),
            file_size=artifact.get("file_size", 0),
            width=artifact.get("width"),
            height=artifact.get("height"),
            metadata=artifact.get("metadata", {}),
        )
        db.add(asset)

    await db.commit()
    
    return {"status": "processed", "job_id": callback.job_id}
