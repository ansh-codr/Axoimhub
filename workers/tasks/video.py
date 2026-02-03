"""
Axiom Design Engine - Video Generation Tasks
Celery tasks for image-to-video and text-to-video generation
"""

from typing import Any
from uuid import uuid4

from workers.celery_app import celery_app
from workers.config import settings
from workers.tasks.base import BaseGenerationTask
from workers.handlers.comfyui import ComfyUIHandler
from workers.utils.logging import get_task_logger


class VideoGenerationTask(BaseGenerationTask):
    """Task for generating videos using video diffusion models."""

    name = "workers.tasks.video.generate_video"
    
    # Video generation needs more time
    soft_time_limit = 1200  # 20 minutes
    time_limit = 1260  # 21 minutes

    def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Execute video generation.
        
        Parameters:
            - width: int (256-2048, default 1024)
            - height: int (256-1080, default 576)
            - num_frames: int (8-720, default 24)
            - fps: int (8-60, default 24)
            - motion_bucket_id: int (1-255, default 127)
            - seed: int | None
            - model: str (default "svd")
            - source_image_path: str | None (for img2vid)
        """
        logger = self.get_logger(job_id)

        # Extract parameters
        width = parameters.get("width", 1024)
        height = parameters.get("height", 576)
        num_frames = min(parameters.get("num_frames", 24), 720)
        fps = parameters.get("fps", 24)
        motion_bucket_id = parameters.get("motion_bucket_id", 127)
        seed = parameters.get("seed")
        model = parameters.get("model", "svd")
        source_image_path = parameters.get("source_image_path")

        logger.info(
            "Starting video generation",
            extra={
                "model": model,
                "dimensions": f"{width}x{height}",
                "frames": num_frames,
                "fps": fps,
            },
        )

        self._update_progress(job_id, 5, "Loading workflow")

        handler = ComfyUIHandler()

        # Determine workflow based on input type
        if source_image_path:
            # Image-to-video (SVD style)
            workflow_name = self._get_img2vid_workflow(model)
            source_data = self.storage_manager.retrieve(source_image_path)
            workflow_params = {
                "source_image": source_data,
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "fps": fps,
                "motion_bucket_id": motion_bucket_id,
                "seed": seed if seed is not None else -1,
            }
        else:
            # Text-to-video (Mochi/CogVideoX style)
            workflow_name = self._get_txt2vid_workflow(model)
            workflow_params = {
                "prompt": prompt,
                "negative_prompt": parameters.get("negative_prompt", ""),
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "fps": fps,
                "seed": seed if seed is not None else -1,
                "guidance_scale": parameters.get("guidance_scale", 7.0),
            }

        self._update_progress(job_id, 10, "Executing workflow")

        def progress_callback(progress: int):
            mapped_progress = 10 + int(progress * 0.8)
            self._update_progress(job_id, mapped_progress, "Generating frames")

        output_videos = handler.execute_workflow(
            workflow_name=workflow_name,
            parameters=workflow_params,
            progress_callback=progress_callback,
            timeout=self.soft_time_limit,
        )

        self._update_progress(job_id, 95, "Encoding video")

        # Store generated videos
        artifacts = []
        for i, video_data in enumerate(output_videos):
            asset_id = str(uuid4())
            filename = f"video_{i+1}.mp4"

            artifact = self._store_artifact(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                data=video_data,
                filename=filename,
                mime_type="video/mp4",
            )

            duration = num_frames / fps

            artifact.update({
                "asset_id": asset_id,
                "asset_type": "video",
                "width": width,
                "height": height,
                "duration": duration,
                "metadata": {
                    "model": model,
                    "prompt": prompt,
                    "num_frames": num_frames,
                    "fps": fps,
                    "motion_bucket_id": motion_bucket_id,
                    "seed": seed,
                },
            })

            artifacts.append(artifact)

        logger.info(f"Generated {len(artifacts)} videos")
        return artifacts

    def _get_img2vid_workflow(self, model: str) -> str:
        """Get workflow name for image-to-video model."""
        workflow_map = {
            "svd": "svd_img2vid",
            "svd_xt": "svd_xt_img2vid",
        }
        return workflow_map.get(model, "svd_img2vid")

    def _get_txt2vid_workflow(self, model: str) -> str:
        """Get workflow name for text-to-video model."""
        workflow_map = {
            "mochi": "mochi_txt2vid",
            "cogvideo": "cogvideo_txt2vid",
            "animatediff": "animatediff_txt2vid",
        }
        return workflow_map.get(model, "mochi_txt2vid")


# Register task
generate_video = celery_app.register_task(VideoGenerationTask())


@celery_app.task(
    name="workers.tasks.video.generate_video_from_image",
    bind=True,
    base=BaseGenerationTask,
    soft_time_limit=1200,
    time_limit=1260,
)
def generate_video_from_image(
    self,
    job_id: str,
    user_id: str,
    project_id: str,
    source_image_path: str,
    prompt: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate video from a source image using Stable Video Diffusion.
    
    Parameters:
        - source_image_path: Path to source image
        - motion_bucket_id: int (1-255, controls motion amount)
        - noise_aug_strength: float (0.0-1.0, default 0.02)
        - fps: int (frames per second for output)
        - num_frames: int (number of frames to generate)
    """
    parameters = parameters or {}
    logger = get_task_logger(__name__, job_id=job_id)

    logger.info(
        "Starting image-to-video generation",
        extra={"source": source_image_path},
    )

    # Delegate to main video task with source image
    parameters["source_image_path"] = source_image_path
    
    task = VideoGenerationTask()
    return task.run(
        job_id=job_id,
        user_id=user_id,
        project_id=project_id,
        prompt=prompt or "",
        parameters=parameters,
    )
