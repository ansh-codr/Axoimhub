"""
Axiom Design Engine - Worker Base Task
Base task class with common functionality for all generation tasks
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from celery import Task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from workers.celery_app import celery_app
from workers.config import settings
from workers.utils.gpu import GPUManager
from workers.utils.logging import get_task_logger
from workers.utils.storage import StorageManager


class BaseGenerationTask(Task, ABC):
    """
    Base class for all generation tasks.
    Provides common functionality for job lifecycle, error handling, and status updates.
    """

    # Task configuration
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True
    max_retries = settings.job_max_retries
    default_retry_delay = settings.job_retry_delay_seconds
    soft_time_limit = settings.job_timeout_seconds - 60
    time_limit = settings.job_timeout_seconds

    # Class attributes
    _gpu_manager: GPUManager | None = None
    _storage_manager: StorageManager | None = None

    @property
    def gpu_manager(self) -> GPUManager:
        """Lazy initialization of GPU manager."""
        if self._gpu_manager is None:
            self._gpu_manager = GPUManager()
        return self._gpu_manager

    @property
    def storage_manager(self) -> StorageManager:
        """Lazy initialization of storage manager."""
        if self._storage_manager is None:
            self._storage_manager = StorageManager()
        return self._storage_manager

    def get_logger(self, job_id: str):
        """Get a logger with job context."""
        return get_task_logger(self.name, job_id=job_id)

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called before task execution starts."""
        job_id = kwargs.get("job_id") or (args[0] if args else "unknown")
        logger = self.get_logger(job_id)
        logger.info(f"Task {self.name} starting", extra={"task_id": task_id})

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called when task succeeds."""
        job_id = kwargs.get("job_id") or (args[0] if args else "unknown")
        logger = self.get_logger(job_id)
        logger.info(f"Task {self.name} completed successfully", extra={"task_id": task_id})

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Called when task fails permanently."""
        job_id = kwargs.get("job_id") or (args[0] if args else "unknown")
        logger = self.get_logger(job_id)
        logger.error(
            f"Task {self.name} failed permanently: {exc}",
            extra={"task_id": task_id, "error": str(exc)},
            exc_info=True,
        )
        # Update job status to failed
        self._update_job_status(job_id, "failed", error_message=str(exc))

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Called when task is retried."""
        job_id = kwargs.get("job_id") or (args[0] if args else "unknown")
        logger = self.get_logger(job_id)
        retry_count = self.request.retries
        logger.warning(
            f"Task {self.name} retrying (attempt {retry_count + 1}): {exc}",
            extra={"task_id": task_id, "retry_count": retry_count},
        )

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int | None = None,
        error_message: str | None = None,
        worker_id: str | None = None,
    ) -> None:
        """
        Update job status in the backend.
        Sends callback to backend API.
        """
        from workers.tasks.callbacks import update_job_status
        
        update_job_status.delay(
            job_id=job_id,
            status=status,
            progress=progress,
            error_message=error_message,
            worker_id=worker_id or self.request.hostname,
        )

    def _update_progress(self, job_id: str, progress: int, message: str | None = None) -> None:
        """Update job progress."""
        self._update_job_status(job_id, "running", progress=progress)
        logger = self.get_logger(job_id)
        logger.info(f"Progress: {progress}%", extra={"progress": progress, "message": message})

    def _store_artifact(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        data: bytes,
        filename: str,
        mime_type: str,
    ) -> dict[str, Any]:
        """
        Store generated artifact and return metadata.
        """
        storage_path = self.storage_manager.store(
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            filename=filename,
            data=data,
        )

        return {
            "storage_path": storage_path,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": len(data),
        }

    @abstractmethod
    def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Execute the generation task.
        
        Args:
            job_id: Unique job identifier
            user_id: Owner's user ID
            project_id: Parent project ID
            prompt: Generation prompt
            parameters: Task-specific parameters
            
        Returns:
            List of artifact metadata dictionaries
        """
        pass

    def run(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        negative_prompt: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Main task execution method.
        Handles lifecycle, error handling, and status updates.
        """
        logger = self.get_logger(job_id)
        parameters = parameters or {}
        if negative_prompt:
            parameters["negative_prompt"] = negative_prompt

        start_time = time.time()

        try:
            # Update status to running
            self._update_job_status(
                job_id,
                "running",
                progress=0,
                worker_id=self.request.hostname,
            )

            # Check GPU availability
            if settings.execution_mode in ("local", "auto"):
                gpu_info = self.gpu_manager.get_gpu_info()
                logger.info(
                    "GPU info",
                    extra={
                        "available": gpu_info.get("available"),
                        "vram_free_gb": gpu_info.get("vram_free_gb"),
                    },
                )

                # Check if cloud fallback needed
                if (
                    settings.execution_mode == "auto"
                    and settings.cloud_fallback_enabled
                    and gpu_info.get("vram_free_gb", 0) < settings.min_vram_gb
                ):
                    logger.info("Insufficient local VRAM, triggering cloud fallback")
                    return self._execute_cloud_fallback(
                        job_id, user_id, project_id, prompt, parameters
                    )

            # Execute the generation
            artifacts = self.execute(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                prompt=prompt,
                parameters=parameters,
            )

            # Update status to completed
            execution_time = time.time() - start_time
            self._update_job_status(job_id, "completed", progress=100)

            logger.info(
                "Generation completed",
                extra={
                    "execution_time": execution_time,
                    "artifact_count": len(artifacts),
                },
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "artifacts": artifacts,
                "execution_time": execution_time,
            }

        except SoftTimeLimitExceeded:
            logger.error("Task exceeded time limit")
            self._update_job_status(
                job_id,
                "failed",
                error_message="Generation timed out",
            )
            raise

        except MaxRetriesExceededError:
            logger.error("Max retries exceeded")
            self._update_job_status(
                job_id,
                "failed",
                error_message="Maximum retry attempts exceeded",
            )
            raise

        except Exception as e:
            logger.exception(f"Generation failed: {e}")
            # Let Celery handle retry logic
            raise self.retry(exc=e)

        finally:
            # Cleanup GPU memory
            self.gpu_manager.cleanup()

    def _execute_cloud_fallback(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute task on cloud GPU provider."""
        from workers.handlers.cloud import CloudExecutionHandler

        handler = CloudExecutionHandler(settings.cloud_provider)
        return handler.execute(
            task_name=self.name,
            job_id=job_id,
            user_id=user_id,
            project_id=project_id,
            prompt=prompt,
            parameters=parameters,
        )
