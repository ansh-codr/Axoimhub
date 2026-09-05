"""
Axiom Design Engine - Base Storage Adapter
Abstract interface for storage backends (Local, S3, MinIO)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseStorageAdapter(ABC):
    """Abstract interface for all storage backend implementations."""

    @abstractmethod
    def generate_signed_url(
        self,
        storage_path: str,
        filename: str,
        expires_in: int = 3600,
        asset_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> str:
        """
        Generate a time-limited signed access/download URL.
        
        Args:
            storage_path: Relative storage path of the artifact
            filename: User-facing filename
            expires_in: Expiration duration in seconds
            asset_id: UUID of asset (for local internal signed URL routing)
            base_url: Optional base API URL
        """
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> bool:
        """
        Delete artifact and any associated metadata from storage.
        
        Args:
            storage_path: Storage path to delete
            
        Returns:
            True if deleted or already absent, False on error
        """
        pass

    @abstractmethod
    def store(
        self,
        storage_path: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Store bytes at storage path."""
        pass

    @abstractmethod
    def retrieve(self, storage_path: str) -> bytes:
        """Retrieve bytes from storage path."""
        pass

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """Check if storage path exists."""
        pass
