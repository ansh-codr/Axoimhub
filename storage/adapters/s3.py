"""
Axiom Design Engine - S3 / MinIO Storage Adapter
Object storage adapter with pre-signed URL generation via boto3
"""

from typing import Any, Optional

from storage.adapters.base import BaseStorageAdapter


class S3StorageAdapter(BaseStorageAdapter):
    """S3/MinIO-compatible storage adapter using boto3."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
        use_ssl: bool = True,
    ):
        self.bucket = bucket_name
        self.endpoint_url = endpoint_url or None
        self.access_key = access_key or None
        self.secret_key = secret_key or None
        self.region = region
        self.use_ssl = use_ssl
        self._client = None

    def _get_client(self):
        """Lazy initialization of boto3 S3 client."""
        if self._client is None:
            import boto3
            from botocore.config import Config

            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                use_ssl=self.use_ssl,
                config=config,
            )
        return self._client

    def generate_signed_url(
        self,
        storage_path: str,
        filename: str,
        expires_in: int = 3600,
        asset_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> str:
        """Generate AWS S3 / MinIO presigned URL."""
        client = self._get_client()
        params = {
            "Bucket": self.bucket,
            "Key": storage_path,
        }
        if filename:
            params["ResponseContentDisposition"] = f'inline; filename="{filename}"'

        return client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def delete(self, storage_path: str) -> bool:
        """Delete object from S3 bucket."""
        client = self._get_client()
        try:
            client.delete_object(
                Bucket=self.bucket,
                Key=storage_path,
            )
            return True
        except Exception:
            return False

    def store(
        self,
        storage_path: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Upload object to S3."""
        client = self._get_client()
        extra_args: dict[str, Any] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = {
                str(k): str(v) for k, v in metadata.items() if v is not None
            }

        client.put_object(
            Bucket=self.bucket,
            Key=storage_path,
            Body=data,
            **extra_args,
        )
        return storage_path

    def retrieve(self, storage_path: str) -> bytes:
        """Retrieve object bytes from S3."""
        client = self._get_client()
        response = client.get_object(
            Bucket=self.bucket,
            Key=storage_path,
        )
        return response["Body"].read()

    def exists(self, storage_path: str) -> bool:
        """Check if object exists in S3."""
        client = self._get_client()
        try:
            client.head_object(
                Bucket=self.bucket,
                Key=storage_path,
            )
            return True
        except Exception:
            return False
