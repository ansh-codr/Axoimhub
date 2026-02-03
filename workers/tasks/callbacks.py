"""
Axiom Design Engine - Callback Tasks
Tasks for updating backend with job status and results
"""

from typing import Any

import httpx

from workers.celery_app import celery_app
from workers.config import settings
from workers.utils.logging import get_task_logger

logger = get_task_logger(__name__)


@celery_app.task(
    name="workers.tasks.callbacks.update_job_status",
    bind=True,
    max_retries=5,
    default_retry_delay=5,
    autoretry_for=(httpx.RequestError,),
)
def update_job_status(
    self,
    job_id: str,
    status: str,
    progress: int | None = None,
    error_message: str | None = None,
    worker_id: str | None = None,
) -> dict[str, Any]:
    """
    Update job status in the backend via API callback.
    
    This task is used to notify the backend of job state changes
    from workers. It runs on a separate queue to avoid blocking
    generation tasks.
    """
    callback_url = f"{settings.backend_api_url}/api/v1/internal/jobs/{job_id}/status"
    
    payload = {
        "status": status,
        "worker_id": worker_id,
    }
    
    if progress is not None:
        payload["progress"] = progress
    
    if error_message:
        # Sanitize error message - don't expose internal details
        sanitized_message = _sanitize_error_message(error_message)
        payload["error_message"] = sanitized_message

    headers = {
        "Content-Type": "application/json",
        "X-Worker-Key": settings.backend_api_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.patch(
                callback_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            logger.info(
                f"Job status updated: {job_id} -> {status}",
                extra={"job_id": job_id, "status": status, "progress": progress},
            )
            
            return {"success": True, "job_id": job_id, "status": status}

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to update job status: HTTP {e.response.status_code}",
            extra={"job_id": job_id, "error": str(e)},
        )
        raise

    except httpx.RequestError as e:
        logger.error(
            f"Failed to connect to backend: {e}",
            extra={"job_id": job_id},
        )
        raise self.retry(exc=e)


@celery_app.task(
    name="workers.tasks.callbacks.register_asset",
    bind=True,
    max_retries=5,
    default_retry_delay=5,
)
def register_asset(
    self,
    job_id: str,
    asset_id: str,
    asset_type: str,
    storage_path: str,
    filename: str,
    mime_type: str,
    file_size: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Register a generated asset in the backend database.
    
    Called after an artifact is successfully stored to create
    the database record linking it to the job.
    """
    callback_url = f"{settings.backend_api_url}/api/v1/internal/assets"
    
    payload = {
        "job_id": job_id,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "storage_path": storage_path,
        "filename": filename,
        "mime_type": mime_type,
        "file_size": file_size,
        "metadata": metadata or {},
    }

    # Add dimensions if available
    if metadata:
        if "width" in metadata:
            payload["width"] = metadata["width"]
        if "height" in metadata:
            payload["height"] = metadata["height"]
        if "duration" in metadata:
            payload["duration"] = metadata["duration"]

    headers = {
        "Content-Type": "application/json",
        "X-Worker-Key": settings.backend_api_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                callback_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            logger.info(
                f"Asset registered: {asset_id}",
                extra={"job_id": job_id, "asset_id": asset_id},
            )
            
            return {"success": True, "asset_id": asset_id}

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to register asset: HTTP {e.response.status_code}",
            extra={"job_id": job_id, "asset_id": asset_id},
        )
        raise

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to backend: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="workers.tasks.callbacks.notify_completion",
    bind=True,
    max_retries=3,
)
def notify_completion(
    self,
    job_id: str,
    status: str,
    artifacts: list[dict[str, Any]],
    execution_time: float,
) -> dict[str, Any]:
    """
    Send final completion notification with all artifacts.
    
    This is called at the end of a successful job to register
    all generated artifacts in a single batch.
    """
    # Register each asset
    for artifact in artifacts:
        register_asset.delay(
            job_id=job_id,
            asset_id=artifact.get("asset_id"),
            asset_type=artifact.get("asset_type"),
            storage_path=artifact.get("storage_path"),
            filename=artifact.get("filename"),
            mime_type=artifact.get("mime_type"),
            file_size=artifact.get("file_size"),
            metadata=artifact.get("metadata"),
        )

    # Update final status
    update_job_status.delay(
        job_id=job_id,
        status=status,
        progress=100,
    )

    logger.info(
        f"Job completion notified: {job_id}",
        extra={
            "job_id": job_id,
            "artifact_count": len(artifacts),
            "execution_time": execution_time,
        },
    )

    return {
        "job_id": job_id,
        "status": status,
        "artifact_count": len(artifacts),
    }


def _sanitize_error_message(message: str) -> str:
    """
    Sanitize error messages to avoid exposing internal details.
    """
    # List of patterns to redact
    sensitive_patterns = [
        ("api_key", "API_KEY"),
        ("password", "PASSWORD"),
        ("secret", "SECRET"),
        ("token", "TOKEN"),
        ("/home/", "/****/"),
        ("/root/", "/****/"),
    ]
    
    sanitized = message
    for pattern, replacement in sensitive_patterns:
        if pattern.lower() in sanitized.lower():
            # Simple case-insensitive replacement
            import re
            sanitized = re.sub(
                re.escape(pattern),
                replacement,
                sanitized,
                flags=re.IGNORECASE,
            )

    # Truncate if too long
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [truncated]"

    return sanitized
