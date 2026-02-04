"""
Axiom Design Engine - Application Configuration
Centralized settings management using Pydantic Settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Application Settings
    # =========================================================================
    app_name: str = "Axiom Design Engine"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # =========================================================================
    # API Settings
    # =========================================================================
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 4

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # =========================================================================
    # Database Settings
    # =========================================================================
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "axiom"
    postgres_password: str = ""
    postgres_db: str = "axiom_engine"

    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        """Construct sync PostgreSQL connection URL (for Alembic)."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    # =========================================================================
    # Redis Settings
    # =========================================================================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @computed_field
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # =========================================================================
    # JWT Authentication Settings
    # =========================================================================
    jwt_secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="Secret key for JWT signing. Generate with: openssl rand -hex 32",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15  # 15 minutes per spec
    jwt_refresh_token_expire_days: int = 7

    # =========================================================================
    # Security Settings
    # =========================================================================
    password_hash_rounds: int = 12
    password_min_length: int = 10
    password_require_special_chars: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    max_upload_size: int = 104857600  # 100MB

    # =========================================================================
    # Storage Settings
    # =========================================================================
    storage_backend: Literal["local", "s3", "minio"] = "local"
    local_storage_path: str = "/data/axiom-storage"

    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "axiom-assets"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = True

    signed_url_expiration: int = 3600  # seconds

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

    # =========================================================================
    # Prompt Enhancer (LLM)
    # =========================================================================
    prompt_enhancer_mode: Literal["rules", "hf"] = "rules"
    prompt_enhancer_endpoint: str = ""
    prompt_enhancer_api_key: str = ""
    prompt_enhancer_model: str = ""
    prompt_enhancer_timeout_seconds: int = 30
    prompt_enhancer_max_new_tokens: int = 120
    prompt_enhancer_temperature: float = 0.7
    prompt_enhancer_top_p: float = 0.95

    # =========================================================================
    # Worker Settings
    # =========================================================================
    execution_mode: Literal["local", "cloud", "auto"] = "local"
    job_timeout_seconds: int = 600
    job_max_retries: int = 3
    job_retry_delay_seconds: int = 30
    
    # Internal API key for worker callbacks
    worker_api_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="API key for worker callback authentication",
    )

    # =========================================================================
    # Generation Limits
    # =========================================================================
    max_image_resolution: int = 2048
    max_video_duration_seconds: int = 30
    max_video_frames: int = 720

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
