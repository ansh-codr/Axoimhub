"""
Axiom Design Engine - Image Generation Tasks
Celery tasks for text-to-image and image-to-image generation
"""

import io
from typing import Any
from uuid import uuid4

from workers.celery_app import celery_app
from workers.config import settings
from workers.tasks.base import BaseGenerationTask
from workers.handlers.comfyui import ComfyUIHandler
from workers.utils.logging import get_task_logger


class ImageGenerationTask(BaseGenerationTask):
    """Task for generating images using Stable Diffusion models."""

    name = "workers.tasks.image.generate_image"

    def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Execute image generation.
        
        Parameters:
            - width: int (256-2048, default 1024)
            - height: int (256-2048, default 1024)
            - num_inference_steps: int (1-100, default 30)
            - guidance_scale: float (1.0-20.0, default 7.5)
            - seed: int | None
            - model: str (default "sdxl")
            - scheduler: str (default "euler")
            - negative_prompt: str | None
            - num_images: int (1-4, default 1)
        """
        logger = self.get_logger(job_id)

        # Extract parameters with defaults
        width = parameters.get("width", 1024)
        height = parameters.get("height", 1024)
        num_inference_steps = parameters.get("num_inference_steps", 30)
        guidance_scale = parameters.get("guidance_scale", 7.5)
        seed = parameters.get("seed")
        model = parameters.get("model", "sdxl")
        scheduler = parameters.get("scheduler", "euler")
        negative_prompt = parameters.get("negative_prompt", "")
        num_images = min(parameters.get("num_images", 1), 4)

        logger.info(
            "Starting image generation",
            extra={
                "model": model,
                "dimensions": f"{width}x{height}",
                "steps": num_inference_steps,
            },
        )

        self._update_progress(job_id, 5, "Loading workflow")

        # Initialize ComfyUI handler
        handler = ComfyUIHandler()

        # Select workflow based on model
        workflow_name = self._get_workflow_name(model)

        # Build workflow parameters
        workflow_params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": num_inference_steps,
            "cfg_scale": guidance_scale,
            "seed": seed if seed is not None else -1,
            "scheduler": scheduler,
            "batch_size": num_images,
        }

        self._update_progress(job_id, 10, "Executing workflow")

        # Execute ComfyUI workflow
        def progress_callback(progress: int):
            # Map ComfyUI progress (0-100) to our range (10-90)
            mapped_progress = 10 + int(progress * 0.8)
            self._update_progress(job_id, mapped_progress, "Generating")

        output_images = handler.execute_workflow(
            workflow_name=workflow_name,
            parameters=workflow_params,
            progress_callback=progress_callback,
        )

        self._update_progress(job_id, 90, "Saving artifacts")

        # Store generated images
        artifacts = []
        for i, image_data in enumerate(output_images):
            asset_id = str(uuid4())
            filename = f"image_{i+1}.png"

            artifact = self._store_artifact(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                data=image_data,
                filename=filename,
                mime_type="image/png",
            )

            artifact.update({
                "asset_id": asset_id,
                "asset_type": "image",
                "width": width,
                "height": height,
                "metadata": {
                    "model": model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "seed": seed,
                    "steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "scheduler": scheduler,
                },
            })

            artifacts.append(artifact)

        logger.info(f"Generated {len(artifacts)} images")
        return artifacts

    def _get_workflow_name(self, model: str) -> str:
        """Get workflow name for the specified model."""
        workflow_map = {
            "sdxl": "sdxl_txt2img",
            "sd15": "sd15_txt2img",
            "sdxl_turbo": "sdxl_turbo_txt2img",
            "flux": "flux_txt2img",
        }
        return workflow_map.get(model, "sdxl_txt2img")


# Register task
generate_image = celery_app.register_task(ImageGenerationTask())


@celery_app.task(
    name="workers.tasks.image.generate_image_variation",
    bind=True,
    base=BaseGenerationTask,
)
def generate_image_variation(
    self,
    job_id: str,
    user_id: str,
    project_id: str,
    source_image_path: str,
    prompt: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate variations of an existing image.
    
    Parameters:
        - source_image_path: Path to source image
        - strength: float (0.0-1.0, default 0.75)
        - Other parameters same as generate_image
    """
    parameters = parameters or {}
    logger = get_task_logger(__name__, job_id=job_id)

    strength = parameters.get("strength", 0.75)
    
    logger.info(
        "Starting image variation",
        extra={"source": source_image_path, "strength": strength},
    )

    # Load source image
    storage = self.storage_manager
    source_data = storage.retrieve(source_image_path)

    # Initialize ComfyUI handler
    handler = ComfyUIHandler()

    # Execute img2img workflow
    workflow_params = {
        "prompt": prompt,
        "negative_prompt": parameters.get("negative_prompt", ""),
        "source_image": source_data,
        "strength": strength,
        "steps": parameters.get("num_inference_steps", 30),
        "cfg_scale": parameters.get("guidance_scale", 7.5),
        "seed": parameters.get("seed", -1),
    }

    output_images = handler.execute_workflow(
        workflow_name="sdxl_img2img",
        parameters=workflow_params,
    )

    # Store artifacts
    artifacts = []
    for i, image_data in enumerate(output_images):
        asset_id = str(uuid4())
        artifact = storage.store(
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            filename=f"variation_{i+1}.png",
            data=image_data,
        )
        artifacts.append({
            "asset_id": asset_id,
            "asset_type": "image",
            "storage_path": artifact,
            "mime_type": "image/png",
        })

    return {
        "job_id": job_id,
        "status": "completed",
        "artifacts": artifacts,
    }
