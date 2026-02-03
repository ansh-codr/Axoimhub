# Schemas Package
from app.schemas.common import (
    BaseSchema,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    AuthenticatedUserResponse,
)
from app.schemas.job import (
    JobTypeEnum,
    JobStatusEnum,
    CreateJobRequest,
    RetryJobRequest,
    JobResponse,
    JobSummaryResponse,
    CreateJobResponse,
    JobProgressUpdate,
    ImageGenerationParams,
    VideoGenerationParams,
    Model3DGenerationParams,
)
from app.schemas.asset import (
    AssetTypeEnum,
    AssetResponse,
    AssetSummaryResponse,
    AssetDownloadResponse,
)
from app.schemas.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)

__all__ = [
    # Common
    "BaseSchema",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
    "SuccessResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "TokenResponse",
    "UserResponse",
    "AuthenticatedUserResponse",
    # Job
    "JobTypeEnum",
    "JobStatusEnum",
    "CreateJobRequest",
    "RetryJobRequest",
    "JobResponse",
    "JobSummaryResponse",
    "CreateJobResponse",
    "JobProgressUpdate",
    "ImageGenerationParams",
    "VideoGenerationParams",
    "Model3DGenerationParams",
    # Asset
    "AssetTypeEnum",
    "AssetResponse",
    "AssetSummaryResponse",
    "AssetDownloadResponse",
    # Project
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "ProjectResponse",
    "ProjectDetailResponse",
    "ProjectSummaryResponse",
]
