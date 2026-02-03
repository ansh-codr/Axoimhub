"""
Axiom Design Engine - Native Model Handler
Handler for models that run directly without ComfyUI (TripoSR, Shap-E, etc.)
"""

import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

import torch

from workers.config import settings
from workers.utils.gpu import GPUManager
from workers.utils.logging import get_task_logger

logger = get_task_logger(__name__)


class BaseModelHandler(ABC):
    """Base class for native model handlers."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.gpu_manager = GPUManager()
        self.device = self._get_device()
        self.models_path = Path(settings.models_cache_path)

    def _get_device(self) -> torch.device:
        """Get the appropriate torch device."""
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @abstractmethod
    def load_model(self) -> None:
        """Load the model into memory."""
        pass

    @abstractmethod
    def generate(
        self,
        input_data: dict[str, Any],
        parameters: dict[str, Any],
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> list[bytes]:
        """Generate output from the model."""
        pass

    def unload_model(self) -> None:
        """Unload model and free memory."""
        self.model = None
        self.gpu_manager.cleanup()


class NativeModelHandler:
    """
    Factory and dispatcher for native model handlers.
    Routes to appropriate handler based on model name.
    """

    _handlers: dict[str, type[BaseModelHandler]] = {}

    @classmethod
    def register(cls, model_name: str, handler_class: type[BaseModelHandler]) -> None:
        """Register a handler for a model."""
        cls._handlers[model_name] = handler_class

    def __init__(self, model_name: str):
        self.model_name = model_name.lower()
        self._handler: BaseModelHandler | None = None

    def _get_handler(self) -> BaseModelHandler:
        """Get or create the appropriate handler."""
        if self._handler is None:
            handler_class = self._handlers.get(self.model_name)
            if handler_class is None:
                # Default fallback handlers
                if "tripo" in self.model_name:
                    self._handler = TripoSRHandler(self.model_name)
                elif "shap" in self.model_name:
                    self._handler = ShapEHandler(self.model_name)
                else:
                    raise ValueError(f"Unknown model: {self.model_name}")
            else:
                self._handler = handler_class(self.model_name)
        return self._handler

    def generate(
        self,
        input_data: dict[str, Any],
        parameters: dict[str, Any],
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> list[bytes]:
        """Generate output using the appropriate handler."""
        handler = self._get_handler()
        return handler.generate(input_data, parameters, progress_callback)


class TripoSRHandler(BaseModelHandler):
    """
    Handler for TripoSR image-to-3D model.
    Converts single images to 3D meshes.
    """

    def load_model(self) -> None:
        """Load TripoSR model."""
        logger.info(f"Loading TripoSR model on {self.device}")
        
        try:
            from tsr.system import TSR
            
            model_path = self.models_path / "triposr"
            self.model = TSR.from_pretrained(
                str(model_path) if model_path.exists() else "stabilityai/TripoSR",
                config_name="config.yaml",
                weight_name="model.ckpt",
            )
            self.model.renderer.set_chunk_size(8192)
            self.model.to(self.device)
            
        except ImportError:
            logger.warning("TSR not installed, using mock model")
            self.model = MockTripoSRModel()

    def generate(
        self,
        input_data: dict[str, Any],
        parameters: dict[str, Any],
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> list[bytes]:
        """Generate 3D mesh from image."""
        if self.model is None:
            self.load_model()

        # Get input image
        image_data = input_data.get("image")
        if image_data is None:
            raise ValueError("No input image provided")

        if progress_callback:
            progress_callback(10, "Processing image")

        # Load and preprocess image
        from PIL import Image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Remove background if requested
        if parameters.get("remove_background", True):
            if progress_callback:
                progress_callback(20, "Removing background")
            image = self._remove_background(image)

        if progress_callback:
            progress_callback(30, "Generating 3D model")

        # Run inference
        with torch.no_grad():
            if hasattr(self.model, "run"):
                scene_codes = self.model.run(
                    image,
                    device=self.device,
                    chunk_size=8192,
                )
            else:
                # Mock model fallback
                scene_codes = self.model(image)

        if progress_callback:
            progress_callback(70, "Extracting mesh")

        # Extract mesh
        output_format = parameters.get("output_format", "glb")
        meshes = self._extract_meshes(scene_codes, output_format, parameters)

        if progress_callback:
            progress_callback(100, "Complete")

        return meshes

    def _remove_background(self, image):
        """Remove background using rembg."""
        try:
            from rembg import remove
            return remove(image)
        except ImportError:
            logger.warning("rembg not installed, skipping background removal")
            return image

    def _extract_meshes(
        self,
        scene_codes,
        output_format: str,
        parameters: dict[str, Any],
    ) -> list[bytes]:
        """Extract and export meshes."""
        meshes = []
        texture_resolution = parameters.get("texture_resolution", 1024)

        for scene_code in scene_codes:
            if hasattr(self.model, "extract_mesh"):
                mesh = self.model.extract_mesh(
                    scene_code,
                    resolution=256,
                    threshold=25.0,
                )
            else:
                # Mock mesh
                mesh = scene_code

            # Export to requested format
            mesh_bytes = self._export_mesh(mesh, output_format, texture_resolution)
            meshes.append(mesh_bytes)

        return meshes

    def _export_mesh(
        self,
        mesh,
        output_format: str,
        texture_resolution: int,
    ) -> bytes:
        """Export mesh to bytes in requested format."""
        buffer = io.BytesIO()

        try:
            import trimesh
            
            if hasattr(mesh, "export"):
                mesh.export(buffer, file_type=output_format)
            else:
                # Create basic trimesh for mock
                vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
                faces = [[0, 1, 2]]
                tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                tri_mesh.export(buffer, file_type=output_format)
                
        except ImportError:
            # Create placeholder GLB
            buffer.write(b"MOCK_GLB_DATA")

        buffer.seek(0)
        return buffer.read()


class ShapEHandler(BaseModelHandler):
    """
    Handler for OpenAI Shap-E text-to-3D model.
    Generates 3D meshes from text prompts.
    """

    def load_model(self) -> None:
        """Load Shap-E model."""
        logger.info(f"Loading Shap-E model on {self.device}")
        
        try:
            from shap_e.diffusion.sample import sample_latents
            from shap_e.models.download import load_model, load_config
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            
            self.xm = load_model("transmitter", device=self.device)
            self.model = load_model("text300M", device=self.device)
            self.diffusion = diffusion_from_config(load_config("diffusion"))
            
        except ImportError:
            logger.warning("Shap-E not installed, using mock model")
            self.model = MockShapEModel()

    def generate(
        self,
        input_data: dict[str, Any],
        parameters: dict[str, Any],
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> list[bytes]:
        """Generate 3D mesh from text prompt."""
        if self.model is None:
            self.load_model()

        prompt = input_data.get("prompt")
        if not prompt:
            raise ValueError("No prompt provided")

        if progress_callback:
            progress_callback(10, "Encoding prompt")

        guidance_scale = parameters.get("guidance_scale", 15.0)
        seed = parameters.get("seed")

        if seed is not None:
            torch.manual_seed(seed)

        if progress_callback:
            progress_callback(20, "Generating latents")

        try:
            from shap_e.diffusion.sample import sample_latents
            from shap_e.util.notebooks import decode_latent_mesh
            
            latents = sample_latents(
                batch_size=1,
                model=self.model,
                diffusion=self.diffusion,
                guidance_scale=guidance_scale,
                model_kwargs=dict(texts=[prompt]),
                progress=True,
                clip_denoised=True,
                use_fp16=True,
                use_karras=True,
                karras_steps=64,
                sigma_min=1e-3,
                sigma_max=160,
                s_churn=0,
            )

            if progress_callback:
                progress_callback(80, "Decoding mesh")

            meshes = []
            for latent in latents:
                mesh = decode_latent_mesh(self.xm, latent).tri_mesh()
                mesh_bytes = self._export_mesh(
                    mesh,
                    parameters.get("output_format", "glb"),
                )
                meshes.append(mesh_bytes)

        except (ImportError, AttributeError):
            # Mock generation
            meshes = [b"MOCK_SHAPE_GLB_DATA"]

        if progress_callback:
            progress_callback(100, "Complete")

        return meshes

    def _export_mesh(self, mesh, output_format: str) -> bytes:
        """Export mesh to bytes."""
        buffer = io.BytesIO()

        try:
            import trimesh
            
            if hasattr(mesh, "verts") and hasattr(mesh, "faces"):
                tri_mesh = trimesh.Trimesh(
                    vertices=mesh.verts,
                    faces=mesh.faces,
                )
                tri_mesh.export(buffer, file_type=output_format)
            else:
                mesh.export(buffer, file_type=output_format)
                
        except (ImportError, AttributeError):
            buffer.write(b"MOCK_GLB_DATA")

        buffer.seek(0)
        return buffer.read()


class MockTripoSRModel:
    """Mock TripoSR model for testing without GPU."""

    def __call__(self, image):
        """Return mock scene codes."""
        return [{"mock": True}]


class MockShapEModel:
    """Mock Shap-E model for testing without GPU."""
    pass


# Register default handlers
NativeModelHandler.register("triposr", TripoSRHandler)
NativeModelHandler.register("shap-e", ShapEHandler)
