"""
Axiom Design Engine - Local Storage Adapter
Filesystem storage adapter with HMAC-signed time-limited internal URLs
"""

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from storage.adapters.base import BaseStorageAdapter


class LocalStorageAdapter(BaseStorageAdapter):
    """Local filesystem storage adapter with HMAC-signed URL generation."""

    def __init__(
        self,
        base_path: str = "/data/axiom-storage",
        secret_key: str = "CHANGE-ME-IN-PRODUCTION",
    ):
        self.base_path = Path(base_path)
        self.secret_key = secret_key

    def _compute_signature(self, identifier: str, expires_at: int) -> str:
        """Compute HMAC-SHA256 signature for identifier and expiration."""
        payload = f"{identifier}:{expires_at}".encode("utf-8")
        return hmac.new(
            self.secret_key.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, identifier: str, expires_at: int, signature: str) -> bool:
        """Verify HMAC signature and check that it has not expired."""
        if int(time.time()) > expires_at:
            return False
        expected = self._compute_signature(identifier, expires_at)
        return hmac.compare_digest(expected, signature)

    def generate_signed_url(
        self,
        storage_path: str,
        filename: str,
        expires_in: int = 3600,
        asset_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> str:
        """
        Generate time-limited HMAC-signed URL for local asset access.
        """
        identifier = asset_id or storage_path
        expires_at = int(time.time()) + expires_in
        sig = self._compute_signature(identifier, expires_at)

        endpoint_base = base_url.rstrip("/") if base_url else ""
        if asset_id:
            return f"{endpoint_base}/api/v1/assets/{asset_id}/file?expires={expires_at}&signature={sig}"
        return f"{endpoint_base}/api/v1/assets/raw/{storage_path}?expires={expires_at}&signature={sig}"

    def get_absolute_path(self, storage_path: str) -> Path:
        """Get validated absolute filesystem path."""
        full_path = (self.base_path / storage_path).resolve()
        return full_path

    def delete(self, storage_path: str) -> bool:
        """Delete file and its metadata sidecar from disk."""
        try:
            full_path = self.get_absolute_path(storage_path)
            deleted = False
            if full_path.is_file():
                full_path.unlink()
                deleted = True

            sidecar = full_path.with_suffix(full_path.suffix + ".json")
            if sidecar.is_file():
                sidecar.unlink()

            return deleted
        except Exception:
            return False

    def store(
        self,
        storage_path: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Store bytes to local disk."""
        full_path = self.get_absolute_path(storage_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)

        if metadata:
            sidecar = full_path.with_suffix(full_path.suffix + ".json")
            with open(sidecar, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        return str(storage_path)

    def retrieve(self, storage_path: str) -> bytes:
        """Read bytes from local disk."""
        full_path = self.get_absolute_path(storage_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def exists(self, storage_path: str) -> bool:
        """Check if file exists on disk."""
        return self.get_absolute_path(storage_path).is_file()
