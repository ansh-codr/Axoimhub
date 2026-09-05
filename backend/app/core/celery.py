"""
Axiom Design Engine - Backend Celery Client
Job dispatching and task lifecycle management
"""

from functools import lru_cache
from typing import Any, Optional
from celery import Celery

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_celery_client() -> Celery:
    """Get or create singleton Celery client for job dispatching."""
    app = Celery(
        "axiom_backend",
        broker=settings.redis_url,
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
    return app


def dispatch_celery_job(
    job_id: str,
    job_type: str,
    user_id: str,
    project_id: str,
    prompt: str,
    negative_prompt: Optional[str] = None,
    parameters: Optional[dict[str, Any]] = None,
    priority: int = 5,
) -> str:
    """
    Publish a generation job to the appropriate Celery queue.
    
    Routing:
      image -> queue_image (workers.tasks.image.generate_image)
      video -> queue_video (workers.tasks.video.generate_video)
      model3d -> queue_3d (workers.tasks.model3d.generate_3d)
    """
    celery_app = get_celery_client()
    parameters = parameters or {}
    has_source_image = "source_image_path" in parameters

    if job_type in ("image", "IMAGE"):
        queue = "queue_image"
        task_name = (
            "workers.tasks.image.generate_image_variation"
            if has_source_image
            else "workers.tasks.image.generate_image"
        )
    elif job_type in ("video", "VIDEO"):
        queue = "queue_video"
        task_name = (
            "workers.tasks.video.generate_video_from_image"
            if has_source_image
            else "workers.tasks.video.generate_video"
        )
    elif job_type in ("model3d", "model_3d", "MODEL_3D"):
        queue = "queue_3d"
        task_name = (
            "workers.tasks.model3d.generate_3d_from_image"
            if has_source_image
            else "workers.tasks.model3d.generate_3d"
        )
    else:
        queue = "queue_image"
        task_name = "workers.tasks.image.generate_image"

    task_kwargs: dict[str, Any] = {
        "job_id": str(job_id),
        "user_id": str(user_id),
        "project_id": str(project_id),
        "prompt": prompt,
        "negative_prompt": negative_prompt or "",
        "parameters": parameters,
    }

    if has_source_image:
        task_kwargs["source_image_path"] = parameters.get("source_image_path")

    try:
        result = celery_app.send_task(
            task_name,
            kwargs=task_kwargs,
            queue=queue,
            priority=priority,
        )
        task_id = result.id
        logger.info(
            f"Dispatched job {job_id} to queue {queue} ({task_name}) as task {task_id}"
        )

        # Store task ID mapping in Redis synchronously for revocation lookup
        import redis
        r = redis.from_url(settings.redis_url)
        r.setex(f"axiom:job_task:{job_id}", 86400, task_id)

        return task_id
    except Exception as e:
        logger.error(f"Failed to dispatch job {job_id} to Celery: {e}")
        raise


def cancel_celery_job(job_id: str) -> bool:
    """
    Cancel a running or queued job.
    Sets Redis cancellation flag and revokes Celery task.
    """
    celery_app = get_celery_client()
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        # Set cancellation flag
        r.setex(f"axiom:cancelled:{job_id}", 3600, "1")

        # Lookup task ID
        task_id = r.get(f"axiom:job_task:{job_id}")
        if task_id:
            task_id_str = task_id.decode("utf-8") if isinstance(task_id, bytes) else str(task_id)
            celery_app.control.revoke(task_id_str, terminate=True, signal="SIGTERM")
            logger.info(f"Revoked Celery task {task_id_str} for job {job_id}")

        # Also revoke by job_id
        celery_app.control.revoke(str(job_id), terminate=True, signal="SIGTERM")
        return True
    except Exception as e:
        logger.warning(f"Error sending cancellation for job {job_id}: {e}")
        return False
