"""
Axiom Design Engine - Asset Routes
Asset retrieval, download, and management
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession, OptionalUser
from app.core.exceptions import AssetNotFoundError, AuthorizationError
from app.models.asset import Asset, AssetType
from app.models.job import Job
from app.models.project import Project
from app.schemas.asset import (
    AssetDownloadResponse,
    AssetResponse,
    AssetSummaryResponse,
    AssetTypeEnum,
)
from app.schemas.common import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/assets", tags=["Assets"])


def generate_signed_url(asset: Asset) -> str:
    """
    Generate a signed URL for asset access.
    In production, this would generate an S3 pre-signed URL.
    """
    # TODO: Implement actual signed URL generation based on storage backend
    # For now, return a placeholder URL structure
    base_url = f"http://localhost:{settings.backend_port}"
    return f"{base_url}/api/v1/assets/{asset.id}/file"


def generate_thumbnail_url(asset: Asset) -> str | None:
    """Generate thumbnail URL for supported asset types."""
    if asset.asset_type in (AssetType.IMAGE, AssetType.VIDEO):
        base_url = f"http://localhost:{settings.backend_port}"
        return f"{base_url}/api/v1/assets/{asset.id}/thumbnail"
    return None


@router.get(
    "",
    response_model=PaginatedResponse[AssetSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Assets",
    description="List assets with optional filtering and pagination.",
)
async def list_assets(
    user: CurrentUser,
    db: DbSession,
    job_id: Annotated[UUID | None, Query(description="Filter by job")] = None,
    asset_type: Annotated[
        AssetTypeEnum | None, Query(description="Filter by asset type")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[AssetSummaryResponse]:
    """
    List user's assets with filtering and pagination.

    - **job_id**: Filter by specific job
    - **asset_type**: Filter by type (image, video, model3d)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    # Base query - only user's assets through project ownership
    query = (
        select(Asset)
        .join(Job)
        .join(Project)
        .where(Project.user_id == user.id)
    )

    # Apply filters
    if job_id:
        query = query.where(Asset.job_id == job_id)

    if asset_type:
        type_map = {
            "image": AssetType.IMAGE,
            "video": AssetType.VIDEO,
            "model3d": AssetType.MODEL_3D,
        }
        query = query.where(Asset.asset_type == type_map[asset_type.value])

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.order_by(Asset.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    assets = result.scalars().all()

    # Convert to response
    items = [
        AssetSummaryResponse(
            id=asset.id,
            asset_type=asset.asset_type.value,
            filename=asset.filename,
            file_size=asset.file_size,
            thumbnail_url=generate_thumbnail_url(asset),
            created_at=asset.created_at,
        )
        for asset in assets
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Asset Details",
    description="Get detailed information about a specific asset.",
)
async def get_asset(
    asset_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> AssetResponse:
    """
    Get asset details including signed access URL.

    - **asset_id**: UUID of the asset to retrieve

    Returns full asset metadata with signed download URL.
    """
    # Get asset with job and project for ownership check
    result = await db.execute(
        select(Asset)
        .options(
            selectinload(Asset.job).selectinload(Job.project)
        )
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise AssetNotFoundError(str(asset_id))

    # Verify ownership
    if asset.job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this asset")

    return AssetResponse(
        id=asset.id,
        job_id=asset.job_id,
        asset_type=asset.asset_type.value,
        filename=asset.filename,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        width=asset.width,
        height=asset.height,
        duration=asset.duration,
        metadata=asset.metadata,
        url=generate_signed_url(asset),
        created_at=asset.created_at,
    )


@router.get(
    "/{asset_id}/download",
    response_model=AssetDownloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Download URL",
    description="Get a signed download URL for the asset.",
)
async def get_download_url(
    asset_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> AssetDownloadResponse:
    """
    Get a signed URL for downloading the asset.

    - **asset_id**: UUID of the asset

    Returns download URL with expiration time.
    """
    # Get asset with ownership check
    result = await db.execute(
        select(Asset)
        .options(
            selectinload(Asset.job).selectinload(Job.project)
        )
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise AssetNotFoundError(str(asset_id))

    if asset.job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this asset")

    return AssetDownloadResponse(
        id=asset.id,
        filename=asset.filename,
        download_url=generate_signed_url(asset),
        expires_in=settings.signed_url_expiration,
    )


@router.delete(
    "/{asset_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Asset",
    description="Delete an asset and its associated file.",
)
async def delete_asset(
    asset_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> SuccessResponse:
    """
    Delete an asset.

    - **asset_id**: UUID of the asset to delete

    This will remove the asset record and the associated file from storage.
    """
    # Get asset with ownership check
    result = await db.execute(
        select(Asset)
        .options(
            selectinload(Asset.job).selectinload(Job.project)
        )
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if asset is None:
        raise AssetNotFoundError(str(asset_id))

    if asset.job.project.user_id != user.id:
        raise AuthorizationError("You do not have access to this asset")

    # TODO: Delete file from storage backend
    # storage_service.delete(asset.storage_path)

    # Delete database record
    await db.delete(asset)
    await db.commit()

    return SuccessResponse(message="Asset deleted successfully")
