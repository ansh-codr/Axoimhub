"""
Axiom Design Engine - Job Dispatcher
Service for dispatching jobs to appropriate queues and tasks
"""

from typing import Any, Literal
from uuid import UUID

from workers.celery_app import celery_app
from workers.tasks.image import generate_image, generate_image_variation
from workers.tasks.video import generate_video, generate_video_from_image
from workers.tasks.model3d import generate_3d, generate_3d_from_image, generate_3d_from_text


JobType = Literal["image", "video", "model3d"]


class JobDispatcher:
    """
    Dispatcher for routing jobs to appropriate Celery tasks.
    """

    # Task mapping by job type
    TASK_MAP = {
        "image": {
            "default": generate_image,
            "variation": generate_image_variation,
            "text_to_image": generate_image,
            "image_to_image": generate_image_variation,
        },
        "video": {
            "default": generate_video,
            "text_to_video": generate_video,
            "image_to_video": generate_video_from_image,
        },
        "model3d": {
            "default": generate_3d,
            "text_to_3d": generate_3d_from_text,
            "image_to_3d": generate_3d_from_image,
        },
    }

    # Queue routing
    QUEUE_MAP = {
        "image": "queue_image",
        "video": "queue_video",
        "model3d": "queue_3d",
    }

    @classmethod
    def dispatch(
        cls,
        job_id: str,
        job_type: JobType,
        user_id: str,
        project_id: str,
        prompt: str,
        negative_prompt: str | None = None,
        parameters: dict[str, Any] | None = None,
        priority: int = 5,
    ) -> str:
        """
        Dispatch a job to the appropriate queue.
        
        Args:
            job_id: Unique job identifier
            job_type: Type of job (image, video, model3d)
            user_id: User who owns the job
            project_id: Project the job belongs to
            prompt: Generation prompt
            negative_prompt: Optional negative prompt
            parameters: Task-specific parameters
            priority: Job priority (1-10, 10 highest)
            
        Returns:
            Celery task ID
        """
        parameters = parameters or {}

        # Determine task variant
        task_variant = cls._determine_variant(job_type, parameters)
        
        # Get task
        task = cls.TASK_MAP.get(job_type, {}).get(task_variant)
        if task is None:
            task = cls.TASK_MAP.get(job_type, {}).get("default")
        
        if task is None:
            raise ValueError(f"Unknown job type: {job_type}")

        # Get queue
        queue = cls.QUEUE_MAP.get(job_type, "queue_image")

        # Prepare task arguments
        task_kwargs = {
            "job_id": job_id,
            "user_id": user_id,
            "project_id": project_id,
            "prompt": prompt,
            "parameters": parameters,
        }

        if negative_prompt:
            task_kwargs["negative_prompt"] = negative_prompt

        # Special handling for specific variants
        if task_variant == "image_to_video" and "source_image_path" in parameters:
            task_kwargs["source_image_path"] = parameters.pop("source_image_path")
        
        if task_variant == "image_to_3d" and "source_image_path" in parameters:
            task_kwargs["source_image_path"] = parameters.pop("source_image_path")
            task_kwargs.pop("prompt", None)  # Not used for img2mesh

        # Submit task
        result = task.apply_async(
            kwargs=task_kwargs,
            queue=queue,
            priority=priority,
        )

        return result.id

    @classmethod
    def _determine_variant(
        cls,
        job_type: JobType,
        parameters: dict[str, Any],
    ) -> str:
        """Determine task variant based on parameters."""
        has_source_image = "source_image_path" in parameters

        if job_type == "image":
            if has_source_image:
                return "image_to_image"
            return "text_to_image"

        elif job_type == "video":
            if has_source_image:
                return "image_to_video"
            return "text_to_video"

        elif job_type == "model3d":
            if has_source_image:
                return "image_to_3d"
            return "text_to_3d"

        return "default"

    @classmethod
    def cancel(cls, celery_task_id: str) -> bool:
        """
        Cancel a pending or running job.
        
        Args:
            celery_task_id: The Celery task ID to cancel
            
        Returns:
            True if cancellation was sent successfully
        """
        celery_app.control.revoke(
            celery_task_id,
            terminate=True,
            signal="SIGTERM",
        )
        return True

    @classmethod
    def get_status(cls, celery_task_id: str) -> dict[str, Any]:
        """
        Get the status of a job.
        
        Args:
            celery_task_id: The Celery task ID
            
        Returns:
            Task status information
        """
        result = celery_app.AsyncResult(celery_task_id)
        
        return {
            "task_id": celery_task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() and result.successful() else None,
        }

    @classmethod
    def get_queue_lengths(cls) -> dict[str, int]:
        """
        Get the number of pending tasks in each queue.
        
        Returns:
            Dict mapping queue name to pending task count
        """
        with celery_app.pool.acquire(block=True) as conn:
            queue_lengths = {}
            for queue_name in cls.QUEUE_MAP.values():
                try:
                    queue_lengths[queue_name] = conn.default_channel.client.llen(queue_name)
                except Exception:
                    queue_lengths[queue_name] = 0
            return queue_lengths
