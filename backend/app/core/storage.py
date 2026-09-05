"""
Axiom Design Engine - Backend Storage Integration
Adapter access configured with application settings
"""

from functools import lru_cache
from app.core.config import settings
from storage.adapters.base import BaseStorageAdapter
from storage.adapters.local import LocalStorageAdapter
from storage.adapters.s3 import S3StorageAdapter


@lru_cache
def get_storage() -> BaseStorageAdapter:
    """Get initialized storage adapter for backend using app settings."""
    if settings.storage_backend in ("s3", "minio"):
        return S3StorageAdapter(
            bucket_name=settings.s3_bucket_name,
            endpoint_url=settings.s3_endpoint_url or None,
            access_key=settings.s3_access_key or None,
            secret_key=settings.s3_secret_key or None,
            region=settings.s3_region,
            use_ssl=settings.s3_use_ssl,
        )
    return LocalStorageAdapter(
        base_path=settings.local_storage_path,
        secret_key=settings.jwt_secret_key,
    )
