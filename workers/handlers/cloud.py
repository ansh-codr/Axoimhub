"""
Axiom Design Engine - Cloud Execution Handler
Handler for cloud GPU fallback execution (RunPod, Vast.ai, Lambda Labs)
"""

import time
from typing import Any, Literal

import httpx

from workers.config import settings
from workers.utils.logging import get_task_logger

logger = get_task_logger(__name__)


class CloudExecutionError(Exception):
    """Cloud execution error."""
    pass


class CloudExecutionHandler:
    """
    Handler for executing tasks on cloud GPU providers.
    Supports RunPod, Vast.ai, and Lambda Labs.
    """

    def __init__(self, provider: Literal["runpod", "vast", "lambda", "none"]):
        self.provider = provider
        self.api_key = settings.cloud_api_key

        if provider == "none":
            raise CloudExecutionError("Cloud fallback is disabled")

        if not self.api_key:
            raise CloudExecutionError(f"No API key configured for {provider}")

        # Provider-specific configuration
        self._provider_config = {
            "runpod": {
                "base_url": "https://api.runpod.io/v2",
                "endpoint_id": settings.cloud_api_key.split(":")[1] if ":" in settings.cloud_api_key else "",
            },
            "vast": {
                "base_url": "https://vast.ai/api/v0",
            },
            "lambda": {
                "base_url": "https://cloud.lambdalabs.com/api/v1",
            },
        }

    def execute(
        self,
        task_name: str,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a task on cloud GPU.
        
        This method submits the job to the cloud provider and waits for completion.
        """
        logger.info(
            f"Executing on cloud provider: {self.provider}",
            extra={"job_id": job_id, "task": task_name},
        )

        if self.provider == "runpod":
            return self._execute_runpod(
                task_name, job_id, user_id, project_id, prompt, parameters
            )
        elif self.provider == "vast":
            return self._execute_vast(
                task_name, job_id, user_id, project_id, prompt, parameters
            )
        elif self.provider == "lambda":
            return self._execute_lambda(
                task_name, job_id, user_id, project_id, prompt, parameters
            )
        else:
            raise CloudExecutionError(f"Unsupported provider: {self.provider}")

    def _execute_runpod(
        self,
        task_name: str,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute on RunPod serverless."""
        config = self._provider_config["runpod"]
        endpoint_id = config["endpoint_id"]
        
        if not endpoint_id:
            raise CloudExecutionError("RunPod endpoint ID not configured")

        # Prepare payload
        payload = {
            "input": {
                "task": task_name,
                "job_id": job_id,
                "user_id": user_id,
                "project_id": project_id,
                "prompt": prompt,
                "parameters": parameters,
                "callback_url": f"{settings.backend_api_url}/api/v1/internal/cloud-callback",
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Submit job
        run_url = f"{config['base_url']}/{endpoint_id}/run"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(run_url, json=payload, headers=headers)
            response.raise_for_status()
            run_data = response.json()

        run_id = run_data.get("id")
        logger.info(f"RunPod job submitted: {run_id}")

        # Poll for completion
        status_url = f"{config['base_url']}/{endpoint_id}/status/{run_id}"
        
        timeout = settings.job_timeout_seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(status_url, headers=headers)
                response.raise_for_status()
                status_data = response.json()

            status = status_data.get("status")

            if status == "COMPLETED":
                output = status_data.get("output", {})
                logger.info(f"RunPod job completed: {run_id}")
                return output

            elif status == "FAILED":
                error = status_data.get("error", "Unknown error")
                raise CloudExecutionError(f"RunPod execution failed: {error}")

            elif status in ("IN_QUEUE", "IN_PROGRESS"):
                time.sleep(5)
                continue

            else:
                raise CloudExecutionError(f"Unknown status: {status}")

        raise CloudExecutionError("Cloud execution timed out")

    def _execute_vast(
        self,
        task_name: str,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute on Vast.ai."""
        # Vast.ai requires instance management
        # This is a simplified implementation
        config = self._provider_config["vast"]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Find available instance
        search_url = f"{config['base_url']}/bundles"
        search_params = {
            "gpu_ram": "12",  # Minimum 12GB VRAM
            "verified": True,
            "rentable": True,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                search_url,
                params=search_params,
                headers=headers,
            )
            response.raise_for_status()
            offers = response.json().get("offers", [])

        if not offers:
            raise CloudExecutionError("No suitable Vast.ai instances available")

        # Select cheapest offer
        offer = min(offers, key=lambda x: x.get("dph_total", float("inf")))
        
        # Create instance
        create_url = f"{config['base_url']}/asks/{offer['id']}"
        create_payload = {
            "image": "axiomengine/worker:latest",
            "disk": 50,
            "env": {
                "TASK_NAME": task_name,
                "JOB_ID": job_id,
                "USER_ID": user_id,
                "PROJECT_ID": project_id,
                "PROMPT": prompt,
                "PARAMETERS": str(parameters),
                "CALLBACK_URL": f"{settings.backend_api_url}/api/v1/internal/cloud-callback",
            },
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.put(
                create_url,
                json=create_payload,
                headers=headers,
            )
            response.raise_for_status()
            instance_data = response.json()

        instance_id = instance_data.get("new_contract")
        logger.info(f"Vast.ai instance created: {instance_id}")

        # Note: Real implementation would poll for completion
        # and handle instance cleanup
        return {
            "provider": "vast",
            "instance_id": instance_id,
            "status": "submitted",
        }

    def _execute_lambda(
        self,
        task_name: str,
        job_id: str,
        user_id: str,
        project_id: str,
        prompt: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute on Lambda Labs."""
        config = self._provider_config["lambda"]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # List available instance types
        types_url = f"{config['base_url']}/instance-types"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(types_url, headers=headers)
            response.raise_for_status()
            instance_types = response.json().get("data", {})

        # Find available GPU instance
        available_type = None
        for type_name, type_info in instance_types.items():
            regions = type_info.get("regions_with_capacity_available", [])
            if regions and "gpu" in type_name.lower():
                available_type = type_name
                break

        if not available_type:
            raise CloudExecutionError("No Lambda Labs instances available")

        # Launch instance
        launch_url = f"{config['base_url']}/instance-operations/launch"
        launch_payload = {
            "instance_type_name": available_type,
            "region_name": instance_types[available_type]["regions_with_capacity_available"][0]["name"],
            "quantity": 1,
            "ssh_key_names": [],
            "file_system_names": [],
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                launch_url,
                json=launch_payload,
                headers=headers,
            )
            response.raise_for_status()
            launch_data = response.json()

        instance_ids = launch_data.get("data", {}).get("instance_ids", [])
        logger.info(f"Lambda Labs instance launched: {instance_ids}")

        # Note: Real implementation would configure and run the task
        # on the launched instance
        return {
            "provider": "lambda",
            "instance_ids": instance_ids,
            "status": "submitted",
        }

    def cancel(self, provider_job_id: str) -> bool:
        """Cancel a cloud job."""
        try:
            if self.provider == "runpod":
                config = self._provider_config["runpod"]
                endpoint_id = config["endpoint_id"]
                cancel_url = f"{config['base_url']}/{endpoint_id}/cancel/{provider_job_id}"
                
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(cancel_url, headers=headers)
                    return response.status_code == 200

            # Add other providers as needed
            return False

        except Exception as e:
            logger.error(f"Failed to cancel cloud job: {e}")
            return False
