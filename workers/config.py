"""
Axiom Design Engine - Worker Configuration
Settings for Celery workers and GPU execution
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Worker-specific settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Redis / Celery Settings
    # =========================================================================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @computed_field
    @property
    def celery_broker_url(self) -> str:
        """Construct Celery broker URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"

    @computed_field
    @property
    def celery_result_backend(self) -> str:
        """Construct Celery result backend URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/1"

    # =========================================================================
    # Worker Settings
    # =========================================================================
    worker_concurrency: int = Field(
        default=1,
        description="Number of concurrent worker processes (1 for GPU)",
    )
    worker_prefetch_multiplier: int = Field(
        default=1,
        description="Tasks to prefetch per worker",
    )
    worker_max_tasks_per_child: int = Field(
        default=50,
        description="Max tasks before worker restart (memory cleanup)",
    )

    # =========================================================================
    # Job Settings
    # =========================================================================
    job_timeout_seconds: int = Field(
        default=1800,
        description="Maximum job execution time (30 min default)",
    )
    job_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed jobs",
    )
    job_retry_delay_seconds: int = Field(
        default=30,
        description="Delay between retry attempts",
    )

    # =========================================================================
    # GPU Settings
    # =========================================================================
    execution_mode: Literal["local", "cloud", "auto"] = Field(
        default="local",
        description="Execution mode for inference",
    )
    cuda_visible_devices: str = Field(
        default="0",
        description="CUDA device indices to use",
    )
    gpu_memory_fraction: float = Field(
        default=0.9,
        description="Fraction of GPU memory to use",
    )
    min_vram_gb: float = Field(
        default=10.0,
        description="Minimum VRAM required for local execution",
    )

    # =========================================================================
    # ComfyUI Settings
    # =========================================================================
    comfyui_host: str = "localhost"
    comfyui_port: int = 8188

    @computed_field
    @property
    def comfyui_api_url(self) -> str:
        """Construct ComfyUI API URL."""
        return f"http://{self.comfyui_host}:{self.comfyui_port}"

    comfyui_workflows_path: str = Field(
        default="/app/orchestration/workflows",
        description="Path to workflow JSON files",
    )
    comfyui_timeout_seconds: int = Field(
        default=600,
        description="ComfyUI execution timeout",
    )

    # =========================================================================
    # Cloud Fallback Settings
    # =========================================================================
    cloud_provider: Literal["runpod", "vast", "lambda", "none"] = Field(
        default="none",
        description="Cloud GPU provider for fallback",
    )
    cloud_api_key: str = Field(
        default="",
        description="Cloud provider API key",
    )
    cloud_fallback_enabled: bool = Field(
        default=False,
        description="Enable automatic cloud fallback",
    )
    cloud_fallback_threshold_vram: float = Field(
        default=10.0,
        description="VRAM threshold (GB) to trigger cloud fallback",
    )

    # =========================================================================
    # Storage Settings
    # =========================================================================
    storage_backend: Literal["local", "s3", "minio"] = Field(
        default="local",
        description="Storage backend for artifacts",
    )
    local_storage_path: str = Field(
        default="/data/axiom-storage",
        description="Local storage path",
    )
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "axiom-assets"
    s3_region: str = "us-east-1"

    # =========================================================================
    # Backend API Settings (for callbacks)
    # =========================================================================
    backend_api_url: str = Field(
        default="http://localhost:8000",
        description="Backend API URL for callbacks",
    )
    backend_api_key: str = Field(
        default="",
        description="Internal API key for worker callbacks",
    )

    # =========================================================================
    # Model Settings
    # =========================================================================
    models_cache_path: str = Field(
        default="/data/models",
        description="Path to cache downloaded models",
    )

    # =========================================================================
    # Observability
    # =========================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 9091


@lru_cache
def get_settings() -> WorkerSettings:
    """Get cached worker settings instance."""
    return WorkerSettings()


settings = get_settings()
