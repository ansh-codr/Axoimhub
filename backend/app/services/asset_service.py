"""
Axiom Design Engine - Asset Service
Core service for managing generated assets
"""

import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_config import Permission
from app.core.authorization import AuthorizationService
from app.core.config import settings
from app.core.exceptions import (
    AssetNotFoundError,
    AuthorizationError,
    ValidationError,
)
from app.models.asset import Asset, AssetType
from app.models.user import User


class AssetService:
    """
    Service for managing generated assets.
    
    Handles asset storage, retrieval, and metadata management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Asset Creation
    # =========================================================================

    async def create_asset(
        self,
        user_id: UUID,
        project_id: UUID,
        job_id: UUID,
        asset_type: AssetType,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Asset:
        """
        Create a new asset record.
        
        Args:
            user_id: Owner user ID
            project_id: Associated project ID
            job_id: Source job ID
            asset_type: Type of asset
            filename: Original filename
            file_path: Storage path
            file_size: Size in bytes
            mime_type: MIME type
            metadata: Optional metadata
            
        Returns:
            Created Asset instance
        """
        # Detect MIME type if not provided
        if mime_type is None:
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        asset = Asset(
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            asset_type=asset_type,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            metadata=metadata or {},
        )

        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)

        return asset

    # =========================================================================
    # Asset Retrieval
    # =========================================================================

    async def get_asset(self, asset_id: UUID, user: User) -> Asset:
        """
        Get an asset by ID.
        
        Args:
            asset_id: Asset identifier
            user: User requesting the asset
            
        Returns:
            Asset instance
            
        Raises:
            AssetNotFoundError: If asset doesn't exist
            AuthorizationError: If user can't access asset
        """
        asset = await self.db.get(Asset, asset_id)
        
        if asset is None:
            raise AssetNotFoundError(str(asset_id))

        # Check access
        if not AuthorizationService.user_can_access_asset(user, asset.user_id):
            raise AuthorizationError("You don't have access to this asset")

        return asset

    async def list_assets(
        self,
        user: User,
        project_id: UUID | None = None,
        asset_type: AssetType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Asset]:
        """
        List assets with optional filters.
        
        Args:
            user: User requesting assets
            project_id: Optional project filter
            asset_type: Optional type filter
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Asset instances
        """
        conditions = []

        # Users see only their assets, admins see all
        if not user.is_admin:
            conditions.append(Asset.user_id == user.id)

        if project_id:
            conditions.append(Asset.project_id == project_id)
        if asset_type:
            conditions.append(Asset.asset_type == asset_type)

        query = (
            select(Asset)
            .where(and_(*conditions) if conditions else True)
            .order_by(Asset.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Asset Storage
    # =========================================================================

    def get_storage_path(
        self,
        user_id: UUID,
        project_id: UUID,
        asset_type: str,
        filename: str,
    ) -> Path:
        """
        Generate storage path for an asset.
        
        Args:
            user_id: Owner user ID
            project_id: Project ID
            asset_type: Type of asset
            filename: Filename
            
        Returns:
            Full storage path
        """
        base_path = Path(settings.local_storage_path)
        return base_path / str(user_id) / str(project_id) / asset_type / filename

    async def save_file(
        self,
        content: bytes | BinaryIO,
        user_id: UUID,
        project_id: UUID,
        asset_type: str,
        filename: str,
    ) -> tuple[str, int]:
        """
        Save file to storage.
        
        Args:
            content: File content (bytes or file-like object)
            user_id: Owner user ID
            project_id: Project ID
            asset_type: Type of asset
            filename: Filename
            
        Returns:
            Tuple of (storage_path, file_size)
        """
        storage_path = self.get_storage_path(user_id, project_id, asset_type, filename)
        
        # Create directories
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        if isinstance(content, bytes):
            storage_path.write_bytes(content)
            file_size = len(content)
        else:
            with open(storage_path, "wb") as f:
                content.seek(0)
                data = content.read()
                f.write(data)
                file_size = len(data)

        return str(storage_path), file_size

    async def get_file_content(self, asset: Asset) -> bytes:
        """
        Get file content from storage.
        
        Args:
            asset: Asset to retrieve
            
        Returns:
            File content as bytes
        """
        storage_path = Path(asset.file_path)
        
        if not storage_path.exists():
            raise AssetNotFoundError(f"File not found: {asset.file_path}")

        return storage_path.read_bytes()

    def get_download_url(self, asset: Asset) -> str:
        """
        Generate download URL for an asset.
        
        Args:
            asset: Asset to generate URL for
            
        Returns:
            Download URL
        """
        # For local storage, return API endpoint
        return f"/api/v1/assets/{asset.id}/download"

    def get_preview_url(self, asset: Asset) -> str:
        """
        Generate preview URL for an asset.
        
        Args:
            asset: Asset to generate URL for
            
        Returns:
            Preview URL
        """
        return f"/api/v1/assets/{asset.id}/preview"

    # =========================================================================
    # Asset Management
    # =========================================================================

    async def delete_asset(self, asset_id: UUID, user: User) -> None:
        """
        Delete an asset.
        
        Args:
            asset_id: Asset identifier
            user: User requesting deletion
        """
        asset = await self.get_asset(asset_id, user)

        # Delete file from storage
        storage_path = Path(asset.file_path)
        if storage_path.exists():
            storage_path.unlink()

        # Delete database record
        await self.db.delete(asset)
        await self.db.commit()

    async def update_asset_metadata(
        self,
        asset_id: UUID,
        user: User,
        metadata: dict[str, Any],
    ) -> Asset:
        """
        Update asset metadata.
        
        Args:
            asset_id: Asset identifier
            user: User requesting update
            metadata: New metadata to merge
            
        Returns:
            Updated Asset instance
        """
        asset = await self.get_asset(asset_id, user)
        
        asset.metadata = {**(asset.metadata or {}), **metadata}
        asset.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(asset)

        return asset
