"""
Axiom Design Engine - ComfyUI Client
Async client for ComfyUI server communication
"""

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator
from uuid import uuid4

import httpx
import websockets
from websockets.exceptions import ConnectionClosed


class ComfyUIClientError(Exception):
    """ComfyUI client error."""
    pass


class ComfyUIClient:
    """
    Async client for ComfyUI API communication.
    
    Usage:
        async with ComfyUIClient("http://localhost:8188") as client:
            prompt_id = await client.queue_prompt(workflow)
            async for event in client.stream_execution(prompt_id):
                print(event)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8188",
        client_id: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or str(uuid4())
        self._http_client: httpx.AsyncClient | None = None
        self._ws_url = self.base_url.replace("http", "ws") + f"/ws?clientId={self.client_id}"

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            raise ComfyUIClientError("Client not initialized. Use 'async with' context.")
        return self._http_client

    # =========================================================================
    # Prompt Management
    # =========================================================================

    async def queue_prompt(
        self,
        workflow: dict[str, Any],
        extra_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Queue a workflow for execution.
        
        Args:
            workflow: ComfyUI workflow dictionary
            extra_data: Optional extra data to pass
            
        Returns:
            Prompt ID for tracking
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }
        
        if extra_data:
            payload["extra_data"] = extra_data

        response = await self.http_client.post("/prompt", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            raise ComfyUIClientError(data["error"])
        
        return data["prompt_id"]

    async def get_history(self, prompt_id: str | None = None) -> dict[str, Any]:
        """
        Get execution history.
        
        Args:
            prompt_id: Optional specific prompt ID
            
        Returns:
            History data
        """
        url = f"/history/{prompt_id}" if prompt_id else "/history"
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_queue(self) -> dict[str, Any]:
        """Get current queue status."""
        response = await self.http_client.get("/queue")
        response.raise_for_status()
        return response.json()

    async def interrupt(self) -> None:
        """Interrupt the current execution."""
        await self.http_client.post("/interrupt")

    async def clear_queue(self, delete_all: bool = False) -> None:
        """
        Clear the execution queue.
        
        Args:
            delete_all: If True, clear running and pending. Otherwise just pending.
        """
        payload = {"clear": delete_all}
        await self.http_client.post("/queue", json=payload)

    # =========================================================================
    # WebSocket Streaming
    # =========================================================================

    async def stream_execution(
        self,
        prompt_id: str,
        timeout: float = 600.0,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream execution events via WebSocket.
        
        Args:
            prompt_id: The prompt ID to monitor
            timeout: Maximum time to wait
            
        Yields:
            Execution events
        """
        try:
            async with websockets.connect(self._ws_url) as ws:
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        raise ComfyUIClientError("Execution timed out")

                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    except asyncio.TimeoutError:
                        continue

                    data = json.loads(message)
                    msg_type = data.get("type")
                    msg_data = data.get("data", {})

                    # Yield relevant events
                    if msg_type == "status":
                        yield {"type": "status", "data": msg_data}

                    elif msg_type == "progress":
                        yield {
                            "type": "progress",
                            "value": msg_data.get("value", 0),
                            "max": msg_data.get("max", 100),
                        }

                    elif msg_type == "executing":
                        if msg_data.get("prompt_id") == prompt_id:
                            node = msg_data.get("node")
                            yield {"type": "executing", "node": node}
                            
                            # None node means execution complete
                            if node is None:
                                yield {"type": "complete", "prompt_id": prompt_id}
                                return

                    elif msg_type == "executed":
                        if msg_data.get("prompt_id") == prompt_id:
                            yield {
                                "type": "executed",
                                "node": msg_data.get("node"),
                                "output": msg_data.get("output"),
                            }

                    elif msg_type == "execution_error":
                        if msg_data.get("prompt_id") == prompt_id:
                            yield {
                                "type": "error",
                                "message": msg_data.get("exception_message"),
                                "node": msg_data.get("node_id"),
                            }
                            raise ComfyUIClientError(
                                msg_data.get("exception_message", "Execution error")
                            )

        except ConnectionClosed:
            raise ComfyUIClientError("WebSocket connection closed unexpectedly")

    # =========================================================================
    # File Management
    # =========================================================================

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        subfolder: str = "",
        overwrite: bool = True,
    ) -> dict[str, str]:
        """
        Upload an image to ComfyUI input folder.
        
        Args:
            image_data: Image bytes
            filename: Target filename
            subfolder: Optional subfolder
            overwrite: Whether to overwrite existing
            
        Returns:
            Dict with name, subfolder, and type
        """
        files = {"image": (filename, image_data, "image/png")}
        data = {
            "overwrite": "true" if overwrite else "false",
        }
        
        if subfolder:
            data["subfolder"] = subfolder

        response = await self.http_client.post(
            "/upload/image",
            files=files,
            data=data,
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_image(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> bytes:
        """
        Download an image from ComfyUI.
        
        Args:
            filename: Image filename
            subfolder: Image subfolder
            folder_type: One of input, output, temp
            
        Returns:
            Image bytes
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }
        
        response = await self.http_client.get(
            "/view",
            params=params,
            timeout=60.0,
        )
        response.raise_for_status()
        return response.content

    # =========================================================================
    # System Info
    # =========================================================================

    async def get_system_stats(self) -> dict[str, Any]:
        """Get system statistics."""
        response = await self.http_client.get("/system_stats")
        response.raise_for_status()
        return response.json()

    async def get_object_info(self, node_class: str | None = None) -> dict[str, Any]:
        """
        Get node object info.
        
        Args:
            node_class: Optional specific node class
            
        Returns:
            Node info dictionary
        """
        url = f"/object_info/{node_class}" if node_class else "/object_info"
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        """Check if ComfyUI server is healthy."""
        try:
            response = await self.http_client.get("/system_stats", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
