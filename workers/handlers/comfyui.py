"""
Axiom Design Engine - ComfyUI Handler
Client for interacting with ComfyUI API in headless mode
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from workers.config import settings
from workers.utils.logging import get_task_logger

logger = get_task_logger(__name__)


class ComfyUIError(Exception):
    """ComfyUI execution error."""

    def __init__(self, message: str, node_id: str | None = None):
        self.message = message
        self.node_id = node_id
        super().__init__(message)


class ComfyUIHandler:
    """
    Handler for ComfyUI workflow execution.
    Communicates with ComfyUI server via HTTP API and WebSocket.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.comfyui_api_url
        self.workflows_path = Path(settings.comfyui_workflows_path)
        self.timeout = settings.comfyui_timeout_seconds
        self.client_id = str(uuid4())

    def execute_workflow(
        self,
        workflow_name: str,
        parameters: dict[str, Any],
        progress_callback: Callable[[int], None] | None = None,
        timeout: int | None = None,
    ) -> list[bytes]:
        """
        Execute a ComfyUI workflow and return generated outputs.
        
        Args:
            workflow_name: Name of workflow JSON file (without .json)
            parameters: Parameters to inject into workflow
            progress_callback: Optional callback for progress updates
            timeout: Optional timeout override
            
        Returns:
            List of output file contents (images/videos as bytes)
        """
        timeout = timeout or self.timeout

        # Load workflow template
        workflow = self._load_workflow(workflow_name)

        # Inject parameters
        workflow = self._inject_parameters(workflow, parameters)

        # Execute synchronously (Celery workers are process-based)
        return asyncio.run(
            self._execute_async(workflow, progress_callback, timeout)
        )

    async def _execute_async(
        self,
        workflow: dict[str, Any],
        progress_callback: Callable[[int], None] | None,
        timeout: int,
    ) -> list[bytes]:
        """Execute workflow asynchronously with WebSocket monitoring."""
        # Queue the prompt
        prompt_id = await self._queue_prompt(workflow)
        logger.info(f"Queued prompt: {prompt_id}")

        # Monitor execution via WebSocket
        outputs = await self._monitor_execution(
            prompt_id,
            progress_callback,
            timeout,
        )

        return outputs

    async def _queue_prompt(self, workflow: dict[str, Any]) -> str:
        """Queue a workflow for execution."""
        url = f"{self.base_url}/prompt"
        
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["prompt_id"]

    async def _monitor_execution(
        self,
        prompt_id: str,
        progress_callback: Callable[[int], None] | None,
        timeout: int,
    ) -> list[bytes]:
        """Monitor workflow execution via WebSocket."""
        ws_url = f"ws://{settings.comfyui_host}:{settings.comfyui_port}/ws?clientId={self.client_id}"
        
        outputs: list[bytes] = []
        start_time = time.time()

        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        raise ComfyUIError("Workflow execution timed out")

                    try:
                        message = await asyncio.wait_for(
                            ws.recv(),
                            timeout=5.0,
                        )
                    except asyncio.TimeoutError:
                        continue

                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "progress":
                        # Progress update
                        progress_data = data.get("data", {})
                        current = progress_data.get("value", 0)
                        total = progress_data.get("max", 100)
                        if progress_callback and total > 0:
                            progress_callback(int(current / total * 100))

                    elif msg_type == "executing":
                        # Node execution update
                        exec_data = data.get("data", {})
                        if exec_data.get("prompt_id") == prompt_id:
                            node_id = exec_data.get("node")
                            if node_id is None:
                                # Execution complete
                                logger.info(f"Workflow execution complete: {prompt_id}")
                                break

                    elif msg_type == "executed":
                        # Node output ready
                        exec_data = data.get("data", {})
                        if exec_data.get("prompt_id") == prompt_id:
                            output_data = exec_data.get("output", {})
                            # Collect image outputs
                            if "images" in output_data:
                                for img in output_data["images"]:
                                    img_data = await self._fetch_output(
                                        img["filename"],
                                        img.get("subfolder", ""),
                                        img.get("type", "output"),
                                    )
                                    outputs.append(img_data)

                    elif msg_type == "execution_error":
                        # Execution failed
                        error_data = data.get("data", {})
                        if error_data.get("prompt_id") == prompt_id:
                            error_msg = error_data.get("exception_message", "Unknown error")
                            node_id = error_data.get("node_id")
                            raise ComfyUIError(error_msg, node_id)

        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            # Try to fetch outputs via HTTP
            outputs = await self._fetch_history_outputs(prompt_id)

        return outputs

    async def _fetch_output(
        self,
        filename: str,
        subfolder: str,
        output_type: str,
    ) -> bytes:
        """Fetch output file from ComfyUI server."""
        url = f"{self.base_url}/view"
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": output_type,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.content

    async def _fetch_history_outputs(self, prompt_id: str) -> list[bytes]:
        """Fetch outputs from history endpoint (fallback)."""
        url = f"{self.base_url}/history/{prompt_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            if response.status_code != 200:
                return []
            
            history = response.json()
            outputs = []
            
            if prompt_id in history:
                prompt_history = history[prompt_id]
                for node_id, node_output in prompt_history.get("outputs", {}).items():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            img_data = await self._fetch_output(
                                img["filename"],
                                img.get("subfolder", ""),
                                img.get("type", "output"),
                            )
                            outputs.append(img_data)
            
            return outputs

    def _load_workflow(self, workflow_name: str) -> dict[str, Any]:
        """Load workflow JSON template."""
        workflow_file = self.workflows_path / f"{workflow_name}.json"
        
        if not workflow_file.exists():
            # Check alternative locations
            alt_paths = [
                self.workflows_path / workflow_name / "workflow.json",
                Path(__file__).parent.parent.parent / "orchestration" / "workflows" / f"{workflow_name}.json",
            ]
            
            for alt_path in alt_paths:
                if alt_path.exists():
                    workflow_file = alt_path
                    break
            else:
                raise ComfyUIError(f"Workflow not found: {workflow_name}")

        with open(workflow_file) as f:
            return json.load(f)

    def _inject_parameters(
        self,
        workflow: dict[str, Any],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Inject parameters into workflow nodes."""
        # Parameter mapping to node inputs
        param_mapping = {
            "prompt": [("positive_prompt", "text"), ("CLIPTextEncode", "text")],
            "negative_prompt": [("negative_prompt", "text"), ("CLIPTextEncodeNegative", "text")],
            "width": [("EmptyLatentImage", "width"), ("KSampler", "latent_image.width")],
            "height": [("EmptyLatentImage", "height"), ("KSampler", "latent_image.height")],
            "steps": [("KSampler", "steps")],
            "cfg_scale": [("KSampler", "cfg")],
            "seed": [("KSampler", "seed")],
            "scheduler": [("KSampler", "scheduler")],
            "batch_size": [("EmptyLatentImage", "batch_size")],
        }

        for param_name, param_value in parameters.items():
            if param_value is None:
                continue

            # Find matching nodes
            mappings = param_mapping.get(param_name, [])
            for node_title, input_name in mappings:
                self._set_node_input(workflow, node_title, input_name, param_value)

        return workflow

    def _set_node_input(
        self,
        workflow: dict[str, Any],
        node_identifier: str,
        input_name: str,
        value: Any,
    ) -> None:
        """Set a node input value by node title or class type."""
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue

            # Match by title or class_type
            meta = node_data.get("_meta", {})
            class_type = node_data.get("class_type", "")
            title = meta.get("title", "")

            if node_identifier in (title, class_type):
                inputs = node_data.get("inputs", {})
                if "." in input_name:
                    # Nested input (e.g., "latent_image.width")
                    parts = input_name.split(".")
                    current = inputs
                    for part in parts[:-1]:
                        current = current.get(part, {})
                    if isinstance(current, dict):
                        current[parts[-1]] = value
                else:
                    inputs[input_name] = value

    def get_queue_status(self) -> dict[str, Any]:
        """Get current queue status from ComfyUI."""
        url = f"{self.base_url}/queue"
        
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()

    def cancel_execution(self, prompt_id: str) -> bool:
        """Cancel a running workflow execution."""
        url = f"{self.base_url}/interrupt"
        
        with httpx.Client() as client:
            response = client.post(url, timeout=10.0)
            return response.status_code == 200

    def clear_queue(self) -> bool:
        """Clear the ComfyUI execution queue."""
        url = f"{self.base_url}/queue"
        
        with httpx.Client() as client:
            response = client.post(
                url,
                json={"clear": True},
                timeout=10.0,
            )
            return response.status_code == 200

    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        overwrite: bool = True,
    ) -> dict[str, str]:
        """
        Upload an image to ComfyUI input folder.
        
        Returns:
            Dict with 'name' and 'subfolder' keys
        """
        url = f"{self.base_url}/upload/image"
        
        files = {
            "image": (filename, image_data, "image/png"),
        }
        data = {
            "overwrite": "true" if overwrite else "false",
        }

        with httpx.Client() as client:
            response = client.post(
                url,
                files=files,
                data=data,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()

    def check_health(self) -> bool:
        """Check if ComfyUI server is healthy."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/system_stats",
                    timeout=5.0,
                )
                return response.status_code == 200
        except httpx.RequestError:
            return False
