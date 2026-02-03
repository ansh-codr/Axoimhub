"""
Axiom Design Engine - 3D Model Generation Tasks
Celery tasks for text-to-3D and image-to-3D generation using ComfyUI workflows
"""

from typing import Any
from uuid import uuid4

from workers.celery_app import celery_app
from workers.config import settings
from workers.tasks.base import BaseGenerationTask
from workers.handlers.comfyui import ComfyUIHandler, ComfyUIError
from workers.utils.logging import get_task_logger


class Model3DGenerationTask(BaseGenerationTask):
    """Task for generating 3D models via ComfyUI workflows."""

    name = "workers.tasks.model3d.generate_3d"
    
    # 3D generation can take longer
    soft_time_limit = 900  # 15 minutes
    time_limit = 960  # 16 minutes

    # Workflow mapping for different generation modes
    WORKFLOW_MAP = {
        "txt2mesh": "triposr_txt2mesh",  # Text → Image → 3D (SDXL + TripoSR)
        "img2mesh": "triposr_img2mesh",  # Image → 3D (TripoSR)
    }

    def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Execute 3D model generation via ComfyUI.
        
        Parameters:
            - output_format: str (glb, obj - default glb)
            - resolution: int (128-512, default 256) - TripoSR mesh resolution
            - threshold: float (0.0-1.0, default 0.5) - Surface threshold
            - remove_background: bool (default True)
            - seed: int | None
            - source_image_path: str | None (for img2mesh)
            - steps: int (default 30) - SDXL sampling steps
            - cfg_scale: float (default 7.5) - SDXL guidance scale
        """
        logger = self.get_logger(job_id)

        # Extract parameters
        output_format = parameters.get("output_format", "glb")
        resolution = parameters.get("resolution", 256)
        threshold = parameters.get("threshold", 0.5)
        remove_background = parameters.get("remove_background", True)
        seed = parameters.get("seed", -1)
        source_image_path = parameters.get("source_image_path")
        steps = parameters.get("steps", 30)
        cfg_scale = parameters.get("cfg_scale", 7.5)

        # Determine workflow based on input
        if source_image_path:
            workflow_name = self.WORKFLOW_MAP["img2mesh"]
            mode = "img2mesh"
        else:
            workflow_name = self.WORKFLOW_MAP["txt2mesh"]
            mode = "txt2mesh"

        logger.info(
            "Starting 3D generation",
            extra={
                "mode": mode,
                "workflow": workflow_name,
                "format": output_format,
                "resolution": resolution,
            },
        )

        self._update_progress(job_id, 5, "Initializing ComfyUI")

        # Initialize ComfyUI handler
        handler = ComfyUIHandler()

        # Prepare workflow parameters
        workflow_params = {
            "resolution": resolution,
            "threshold": threshold,
            "remove_background": remove_background,
        }

        if mode == "img2mesh":
            # Upload source image to ComfyUI
            source_data = self.storage_manager.retrieve(source_image_path)
            upload_result = handler.upload_image(
                source_data,
                f"input_{job_id}.png",
            )
            workflow_params["input_image"] = upload_result["name"]
        else:
            # Text-to-3D: Add SDXL parameters
            workflow_params["prompt"] = prompt
            workflow_params["negative_prompt"] = parameters.get(
                "negative_prompt",
                "blurry, low quality, distorted, noisy background, complex background"
            )
            workflow_params["seed"] = seed
            workflow_params["steps"] = steps
            workflow_params["cfg_scale"] = cfg_scale
            workflow_params["width"] = parameters.get("width", 512)
            workflow_params["height"] = parameters.get("height", 512)

        # Set output paths
        output_base = f"axiom_{job_id}"
        workflow_params["output_glb"] = f"{output_base}.glb"
        workflow_params["output_obj"] = f"{output_base}.obj"

        self._update_progress(job_id, 10, "Executing workflow")

        # Progress callback
        def progress_callback(progress: int):
            # Map 0-100 to 10-90
            mapped_progress = 10 + int(progress * 0.8)
            self._update_progress(job_id, mapped_progress, "Generating 3D model")

        # Execute ComfyUI workflow
        try:
            outputs = handler.execute_workflow(
                workflow_name=workflow_name,
                parameters=workflow_params,
                progress_callback=progress_callback,
            )
        except ComfyUIError as e:
            logger.error(f"ComfyUI error: {e.message}")
            raise

        self._update_progress(job_id, 95, "Saving artifacts")

        # Store generated meshes
        artifacts = []
        
        # Determine which outputs to store based on format
        ext_map = {
            "glb": ("glb", "model/gltf-binary"),
            "obj": ("obj", "text/plain"),
        }
        ext, mime_type = ext_map.get(output_format, ("glb", "model/gltf-binary"))

        for i, mesh_data in enumerate(outputs):
            asset_id = str(uuid4())
            filename = f"model_{i+1}.{ext}"

            artifact = self._store_artifact(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                data=mesh_data,
                filename=filename,
                mime_type=mime_type,
            )

            artifact.update({
                "asset_id": asset_id,
                "asset_type": "model3d",
                "metadata": {
                    "mode": mode,
                    "prompt": prompt,
                    "output_format": output_format,
                    "resolution": resolution,
                    "threshold": threshold,
                    "seed": seed,
                },
            })

            artifacts.append(artifact)

        logger.info(f"Generated {len(artifacts)} 3D models")
        return artifacts


# Register task
generate_3d = celery_app.register_task(Model3DGenerationTask())


@celery_app.task(
    name="workers.tasks.model3d.generate_3d_from_image",
    bind=True,
    base=BaseGenerationTask,
    soft_time_limit=900,
    time_limit=960,
)
def generate_3d_from_image(
    self,
    job_id: str,
    user_id: str,
    project_id: str,
    source_image_path: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate 3D model from a source image using TripoSR via ComfyUI.
    
    Parameters:
        - source_image_path: Path to source image in storage
        - output_format: str (glb, obj - default glb)
        - resolution: int (128-512, default 256)
        - threshold: float (0.0-1.0, default 0.5)
        - remove_background: bool (default True)
    """
    parameters = parameters or {}
    logger = get_task_logger(__name__, job_id=job_id)

    logger.info(
        "Starting image-to-3D generation",
        extra={"source": source_image_path},
    )

    # Configure for img2mesh workflow
    parameters["source_image_path"] = source_image_path
    
    task = Model3DGenerationTask()
    return task.run(
        job_id=job_id,
        user_id=user_id,
        project_id=project_id,
        prompt="",  # Not used for img2mesh
        parameters=parameters,
    )


@celery_app.task(
    name="workers.tasks.model3d.generate_3d_from_text",
    bind=True,
    base=BaseGenerationTask,
    soft_time_limit=900,
    time_limit=960,
)
def generate_3d_from_text(
    self,
    job_id: str,
    user_id: str,
    project_id: str,
    prompt: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate 3D model from text prompt using SDXL + TripoSR pipeline.
    
    This uses a two-stage approach:
    1. Generate a clean 3D-friendly image from the prompt using SDXL
    2. Convert that image to a 3D mesh using TripoSR
    
    Parameters:
        - prompt: Text description of the 3D model
        - output_format: str (glb, obj - default glb)
        - resolution: int (128-512, default 256)
        - steps: int (SDXL sampling steps, default 30)
        - cfg_scale: float (SDXL guidance, default 7.5)
        - seed: int (for reproducibility)
    """
    parameters = parameters or {}
    logger = get_task_logger(__name__, job_id=job_id)

    logger.info(
        "Starting text-to-3D generation",
        extra={"prompt": prompt[:100]},
    )
    
    task = Model3DGenerationTask()
    return task.run(
        job_id=job_id,
        user_id=user_id,
        project_id=project_id,
        prompt=prompt,
        parameters=parameters,
    )
