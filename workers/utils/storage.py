"""
Axiom Design Engine - Storage Manager
Utilities for storing and retrieving generated artifacts
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Literal

from workers.config import settings
from workers.utils.logging import get_task_logger

logger = get_task_logger(__name__)


class StorageError(Exception):
    """Storage operation error."""
    pass


class StorageManager:
    """
    Manager for artifact storage.
    Supports local filesystem and S3-compatible storage.
    """

    def __init__(self, backend: str | None = None):
        self.backend = backend or settings.storage_backend
        self._s3_client = None

    def store(
        self,
        user_id: str,
        project_id: str,
        job_id: str,
        filename: str,
        data: bytes,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store artifact data and return storage path.
        
        Path format: {user_id}/{project_id}/{job_id}/{filename}
        
        Args:
            user_id: User ID
            project_id: Project ID
            job_id: Job ID
            filename: Artifact filename
            data: Binary data to store
            metadata: Optional metadata to store alongside
            
        Returns:
            Storage path for the artifact
        """
        # Build storage path
        storage_path = self._build_path(user_id, project_id, job_id, filename)

        if self.backend == "local":
            self._store_local(storage_path, data, metadata)
        elif self.backend in ("s3", "minio"):
            self._store_s3(storage_path, data, metadata)
        else:
            raise StorageError(f"Unsupported storage backend: {self.backend}")

        logger.info(
            f"Stored artifact: {storage_path}",
            extra={"size": len(data), "backend": self.backend},
        )

        return storage_path

    def retrieve(self, storage_path: str) -> bytes:
        """
        Retrieve artifact data from storage.
        
        Args:
            storage_path: Full storage path
            
        Returns:
            Binary artifact data
        """
        if self.backend == "local":
            return self._retrieve_local(storage_path)
        elif self.backend in ("s3", "minio"):
            return self._retrieve_s3(storage_path)
        else:
            raise StorageError(f"Unsupported storage backend: {self.backend}")

    def delete(self, storage_path: str) -> bool:
        """
        Delete an artifact from storage.
        
        Args:
            storage_path: Full storage path
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if self.backend == "local":
                return self._delete_local(storage_path)
            elif self.backend in ("s3", "minio"):
                return self._delete_s3(storage_path)
            else:
                raise StorageError(f"Unsupported storage backend: {self.backend}")
        except Exception as e:
            logger.error(f"Failed to delete {storage_path}: {e}")
            return False

    def exists(self, storage_path: str) -> bool:
        """Check if an artifact exists."""
        if self.backend == "local":
            full_path = Path(settings.local_storage_path) / storage_path
            return full_path.exists()
        elif self.backend in ("s3", "minio"):
            return self._exists_s3(storage_path)
        return False

    def get_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Get a URL for accessing the artifact.
        
        Args:
            storage_path: Full storage path
            expires_in: URL expiration time in seconds (for S3)
            
        Returns:
            Access URL
        """
        if self.backend == "local":
            # Return relative path for local storage
            return f"/storage/{storage_path}"
        elif self.backend in ("s3", "minio"):
            return self._get_presigned_url(storage_path, expires_in)
        else:
            raise StorageError(f"Unsupported storage backend: {self.backend}")

    def _build_path(
        self,
        user_id: str,
        project_id: str,
        job_id: str,
        filename: str,
    ) -> str:
        """Build storage path following naming convention."""
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        return f"{user_id}/{project_id}/{job_id}/{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path traversal
        filename = os.path.basename(filename)
        # Replace problematic characters
        for char in ['<', '>', ':', '"', '|', '?', '*']:
            filename = filename.replace(char, '_')
        return filename

    # =========================================================================
    # Local Storage Implementation
    # =========================================================================

    def _store_local(
        self,
        storage_path: str,
        data: bytes,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Store to local filesystem."""
        full_path = Path(settings.local_storage_path) / storage_path

        # Create directory
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write data
        with open(full_path, "wb") as f:
            f.write(data)

        # Write metadata sidecar
        if metadata:
            import json
            metadata_path = full_path.with_suffix(full_path.suffix + ".json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

    def _retrieve_local(self, storage_path: str) -> bytes:
        """Retrieve from local filesystem."""
        full_path = Path(settings.local_storage_path) / storage_path

        if not full_path.exists():
            raise StorageError(f"File not found: {storage_path}")

        with open(full_path, "rb") as f:
            return f.read()

    def _delete_local(self, storage_path: str) -> bool:
        """Delete from local filesystem."""
        full_path = Path(settings.local_storage_path) / storage_path

        if not full_path.exists():
            return False

        full_path.unlink()

        # Also delete metadata sidecar if exists
        metadata_path = full_path.with_suffix(full_path.suffix + ".json")
        if metadata_path.exists():
            metadata_path.unlink()

        return True

    # =========================================================================
    # S3 Storage Implementation
    # =========================================================================

    def _get_s3_client(self):
        """Get or create S3 client."""
        if self._s3_client is None:
            import boto3
            from botocore.config import Config

            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url or None,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                config=config,
            )

        return self._s3_client

    def _store_s3(
        self,
        storage_path: str,
        data: bytes,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Store to S3-compatible storage."""
        client = self._get_s3_client()

        # Prepare metadata
        extra_args: dict[str, Any] = {}
        if metadata:
            # S3 metadata must be strings
            extra_args["Metadata"] = {
                k: str(v) for k, v in metadata.items()
                if v is not None
            }

        # Set content type based on extension
        extension = Path(storage_path).suffix.lower()
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".glb": "model/gltf-binary",
            ".obj": "text/plain",
            ".fbx": "application/octet-stream",
        }
        extra_args["ContentType"] = content_types.get(
            extension,
            "application/octet-stream"
        )

        # Upload
        from io import BytesIO
        client.upload_fileobj(
            BytesIO(data),
            settings.s3_bucket_name,
            storage_path,
            ExtraArgs=extra_args,
        )

    def _retrieve_s3(self, storage_path: str) -> bytes:
        """Retrieve from S3-compatible storage."""
        client = self._get_s3_client()

        from io import BytesIO
        buffer = BytesIO()

        try:
            client.download_fileobj(
                settings.s3_bucket_name,
                storage_path,
                buffer,
            )
        except client.exceptions.NoSuchKey:
            raise StorageError(f"File not found: {storage_path}")

        buffer.seek(0)
        return buffer.read()

    def _delete_s3(self, storage_path: str) -> bool:
        """Delete from S3-compatible storage."""
        client = self._get_s3_client()

        try:
            client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=storage_path,
            )
            return True
        except Exception:
            return False

    def _exists_s3(self, storage_path: str) -> bool:
        """Check if object exists in S3."""
        client = self._get_s3_client()

        try:
            client.head_object(
                Bucket=settings.s3_bucket_name,
                Key=storage_path,
            )
            return True
        except Exception:
            return False

    def _get_presigned_url(self, storage_path: str, expires_in: int) -> str:
        """Generate presigned URL for S3 object."""
        client = self._get_s3_client()

        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": storage_path,
            },
            ExpiresIn=expires_in,
        )


def compute_file_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Compute hash of file data."""
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"
