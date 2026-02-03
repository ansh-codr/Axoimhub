"""
Axiom Design Engine - Workflow Adapter
Adapter for loading and parameterizing ComfyUI workflows
"""

import json
from pathlib import Path
from typing import Any

from workers.config import settings


class WorkflowError(Exception):
    """Workflow loading or parameterization error."""
    pass


class WorkflowAdapter:
    """
    Adapter for loading and parameterizing ComfyUI workflow templates.
    
    Usage:
        adapter = WorkflowAdapter("sdxl_txt2img")
        workflow = adapter.build(
            prompt="a beautiful landscape",
            width=1024,
            height=1024,
        )
    """

    # Default parameter to node mapping
    DEFAULT_MAPPINGS = {
        # Prompt inputs
        "prompt": [
            ("positive_prompt", "text"),
            ("CLIPTextEncode", "text"),
        ],
        "negative_prompt": [
            ("negative_prompt", "text"),
        ],
        
        # Dimension inputs
        "width": [
            ("EmptyLatentImage", "width"),
        ],
        "height": [
            ("EmptyLatentImage", "height"),
        ],
        "batch_size": [
            ("EmptyLatentImage", "batch_size"),
        ],
        
        # Sampler inputs
        "seed": [
            ("KSampler", "seed"),
        ],
        "steps": [
            ("KSampler", "steps"),
        ],
        "cfg_scale": [
            ("KSampler", "cfg"),
        ],
        "scheduler": [
            ("KSampler", "scheduler"),
        ],
        "sampler_name": [
            ("KSampler", "sampler_name"),
        ],
        "denoise": [
            ("KSampler", "denoise"),
        ],
        
        # Video inputs
        "num_frames": [
            ("SVD_img2vid_Conditioning", "video_frames"),
        ],
        "fps": [
            ("VHS_VideoCombine", "frame_rate"),
        ],
        "motion_bucket_id": [
            ("SVD_img2vid_Conditioning", "motion_bucket_id"),
        ],
        
        # Model inputs
        "checkpoint": [
            ("CheckpointLoaderSimple", "ckpt_name"),
            ("Load Checkpoint", "ckpt_name"),
        ],
    }

    def __init__(
        self,
        workflow_name: str,
        workflows_path: str | Path | None = None,
        custom_mappings: dict[str, list[tuple[str, str]]] | None = None,
    ):
        """
        Initialize workflow adapter.
        
        Args:
            workflow_name: Name of workflow (without .json extension)
            workflows_path: Path to workflows directory
            custom_mappings: Additional parameter mappings
        """
        self.workflow_name = workflow_name
        self.workflows_path = Path(workflows_path or settings.comfyui_workflows_path)
        
        # Merge custom mappings
        self.mappings = {**self.DEFAULT_MAPPINGS}
        if custom_mappings:
            self.mappings.update(custom_mappings)

        self._template: dict[str, Any] | None = None

    def load_template(self) -> dict[str, Any]:
        """Load workflow template from file."""
        if self._template is not None:
            return self._template

        workflow_file = self.workflows_path / f"{self.workflow_name}.json"
        
        if not workflow_file.exists():
            # Try alternate paths
            alt_paths = [
                self.workflows_path / self.workflow_name / "workflow.json",
                Path(__file__).parent.parent / "workflows" / f"{self.workflow_name}.json",
            ]
            
            for path in alt_paths:
                if path.exists():
                    workflow_file = path
                    break
            else:
                raise WorkflowError(f"Workflow not found: {self.workflow_name}")

        with open(workflow_file) as f:
            self._template = json.load(f)

        return self._template

    def build(self, **parameters) -> dict[str, Any]:
        """
        Build workflow with injected parameters.
        
        Args:
            **parameters: Parameters to inject
            
        Returns:
            Modified workflow dictionary
        """
        # Load and copy template
        template = self.load_template()
        workflow = json.loads(json.dumps(template))  # Deep copy

        # Inject each parameter
        for param_name, param_value in parameters.items():
            if param_value is None:
                continue

            mappings = self.mappings.get(param_name, [])
            for node_identifier, input_name in mappings:
                self._set_node_input(workflow, node_identifier, input_name, param_value)

        return workflow

    def _set_node_input(
        self,
        workflow: dict[str, Any],
        node_identifier: str,
        input_name: str,
        value: Any,
    ) -> bool:
        """
        Set a node input value.
        
        Args:
            workflow: Workflow dictionary
            node_identifier: Node title or class type
            input_name: Input name
            value: Value to set
            
        Returns:
            True if node was found and updated
        """
        found = False
        
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue

            # Match by title or class_type
            meta = node_data.get("_meta", {})
            class_type = node_data.get("class_type", "")
            title = meta.get("title", "")

            if node_identifier in (title, class_type):
                inputs = node_data.get("inputs", {})
                
                if input_name in inputs:
                    inputs[input_name] = value
                    found = True
                elif "widgets_values" in node_data:
                    # Try to update widget values based on position
                    # This is a fallback for some node types
                    pass

        return found

    def get_required_inputs(self) -> dict[str, list[str]]:
        """
        Get required inputs for the workflow.
        
        Returns:
            Dict mapping node titles to required input names
        """
        template = self.load_template()
        required = {}

        for node_id, node_data in template.items():
            if not isinstance(node_data, dict):
                continue

            meta = node_data.get("_meta", {})
            title = meta.get("title", node_data.get("class_type", f"node_{node_id}"))
            
            inputs = node_data.get("inputs", {})
            input_names = [k for k, v in inputs.items() if not isinstance(v, list)]
            
            if input_names:
                required[title] = input_names

        return required


class WorkflowRegistry:
    """
    Registry for workflow adapters.
    """

    _adapters: dict[str, WorkflowAdapter] = {}

    @classmethod
    def register(
        cls,
        name: str,
        workflows_path: str | Path | None = None,
        custom_mappings: dict[str, list[tuple[str, str]]] | None = None,
    ) -> WorkflowAdapter:
        """
        Register a workflow adapter.
        
        Args:
            name: Workflow name
            workflows_path: Custom workflows path
            custom_mappings: Custom parameter mappings
            
        Returns:
            Registered adapter
        """
        adapter = WorkflowAdapter(
            workflow_name=name,
            workflows_path=workflows_path,
            custom_mappings=custom_mappings,
        )
        cls._adapters[name] = adapter
        return adapter

    @classmethod
    def get(cls, name: str) -> WorkflowAdapter:
        """
        Get a workflow adapter.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow adapter
        """
        if name not in cls._adapters:
            cls._adapters[name] = WorkflowAdapter(name)
        return cls._adapters[name]

    @classmethod
    def list_workflows(cls) -> list[str]:
        """List all registered workflow names."""
        return list(cls._adapters.keys())


# Pre-register standard workflows
WorkflowRegistry.register("sdxl_txt2img")
WorkflowRegistry.register("sdxl_img2img")
WorkflowRegistry.register("svd_img2vid")
