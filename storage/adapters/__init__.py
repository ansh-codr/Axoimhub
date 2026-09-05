"""
Axiom Design Engine - Storage Adapters
Factory and registry for storage backends
"""

import os
from functools import lru_cache
from typing import Optional

from storage.adapters.base import BaseStorageAdapter
from storage.adapters.local import LocalStorageAdapter
from storage.adapters.s3 import S3StorageAdapter

__all__ = [
    "BaseStorageAdapter",
    "LocalStorageAdapter",
    "S3StorageAdapter",
    "get_storage_adapter",
]


@lru_cache
def get_storage_adapter(
    backend: Optional[str] = None,
) -> BaseStorageAdapter:
    """
    Get configured singleton storage adapter.
    """
    storage_backend = backend or os.getenv("STORAGE_BACKEND", "local").lower()

    if storage_backend in ("s3", "minio"):
        return S3StorageAdapter(
            bucket_name=os.getenv("S3_BUCKET_NAME", "axiom-assets"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            access_key=os.getenv("S3_ACCESS_KEY") or None,
            secret_key=os.getenv("S3_SECRET_KEY") or None,
            region=os.getenv("S3_REGION", "us-east-1"),
            use_ssl=os.getenv("S3_USE_SSL", "true").lower() in ("true", "1", "yes"),
        )
    else:
        return LocalStorageAdapter(
            base_path=os.getenv("LOCAL_STORAGE_PATH", "/data/axiom-storage"),
            secret_key=os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION"),
        )
