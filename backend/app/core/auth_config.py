"""
Axiom Design Engine - Authentication System Configuration
Safety rules, guardrails, and resource limits
"""

from enum import Enum
from typing import TypedDict


# =============================================================================
# Permission System
# =============================================================================

class Permission(str, Enum):
    """System permissions for RBAC."""

    # Job Management
    CREATE_JOB = "create_job"
    CANCEL_JOB = "cancel_job"
    RETRY_JOB = "retry_job"

    # Asset Management
    VIEW_OWN_ASSETS = "view_own_assets"
    VIEW_ALL_ASSETS = "view_all_assets"
    DOWNLOAD_ASSETS = "download_assets"
    DELETE_ASSETS = "delete_assets"

    # Project Management
    CREATE_PROJECT = "create_project"
    EDIT_PROJECT = "edit_project"
    DELETE_PROJECT = "delete_project"

    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_ALL_JOBS = "view_all_jobs"

    # Worker Management
    MANAGE_WORKERS = "manage_workers"
    EXECUTE_JOBS = "execute_jobs"

    # System Configuration
    SYSTEM_CONFIGURATION = "system_configuration"
    MANAGE_SETTINGS = "manage_settings"

    # Internal Operations
    INTERNAL_CALLBACKS = "internal_callbacks"
    WORKER_STATUS_UPDATES = "worker_status_updates"


# =============================================================================
# Role-Based Access Control (RBAC)
# =============================================================================

ROLE_PERMISSIONS = {
    "user": [
        Permission.CREATE_JOB,
        Permission.CANCEL_JOB,
        Permission.RETRY_JOB,
        Permission.VIEW_OWN_ASSETS,
        Permission.DOWNLOAD_ASSETS,
        Permission.CREATE_PROJECT,
        Permission.EDIT_PROJECT,
        Permission.DELETE_PROJECT,
    ],
    "admin": [
        # All user permissions
        Permission.CREATE_JOB,
        Permission.CANCEL_JOB,
        Permission.RETRY_JOB,
        Permission.VIEW_OWN_ASSETS,
        Permission.DOWNLOAD_ASSETS,
        Permission.DELETE_ASSETS,
        Permission.CREATE_PROJECT,
        Permission.EDIT_PROJECT,
        Permission.DELETE_PROJECT,
        # Admin specific
        Permission.MANAGE_USERS,
        Permission.VIEW_ALL_ASSETS,
        Permission.VIEW_ALL_JOBS,
        Permission.MANAGE_WORKERS,
        Permission.SYSTEM_CONFIGURATION,
        Permission.MANAGE_SETTINGS,
    ],
    "system": [
        # Internal operations only
        Permission.INTERNAL_CALLBACKS,
        Permission.WORKER_STATUS_UPDATES,
        Permission.EXECUTE_JOBS,
    ],
}


# =============================================================================
# Safety & Guardrails Configuration
# =============================================================================

class PromptSanitization(TypedDict, total=False):
    """Prompt sanitization rules."""

    max_length: int
    strip_executable_code: bool
    reject_filesystem_paths: bool
    reject_sql_patterns: bool
    reject_html_tags: bool


# Prompt sanitization config
PROMPT_SANITIZATION: PromptSanitization = {
    "max_length": 4000,
    "strip_executable_code": True,
    "reject_filesystem_paths": True,
    "reject_sql_patterns": True,
    "reject_html_tags": False,  # Allow HTML for proper formatting
}

# Job rate limits
JOB_LIMITS = {
    "max_concurrent_jobs_per_user": 3,
    "max_jobs_per_day": 100,
    "max_jobs_per_hour": 20,
}

# Resource limits
RESOURCE_LIMITS = {
    "max_image_resolution": {
        "width": 2048,
        "height": 2048,
        "megapixels": 4.194,  # 2048x2048 = ~4.19 MP
    },
    "max_video_duration_seconds": 6,
    "max_video_frames": 48,
    "max_video_fps": 8,
    "max_3d_mesh_faces": 200000,
    "max_file_size_mb": 512,
}

# Content restrictions
CONTENT_RESTRICTIONS = {
    "no_identity_impersonation": True,
    "no_biometric_replication": True,
    "no_explicit_content": True,
    "no_violence": True,
    "no_hate_speech": True,
}

# Dangerous patterns that should be blocked
DANGEROUS_PATTERNS = {
    "filesystem_paths": [
        r"^(/|[a-zA-Z]:)",  # Absolute paths (Unix or Windows)
        r"\.\.(/|\\)",  # Path traversal
    ],
    "code_patterns": [
        r"<script[^>]*>",  # JavaScript tags
        r"eval\(",  # eval function
        r"exec\(",  # exec function
        r"__import__",  # Python import
        r"subprocess\.",  # Subprocess execution
    ],
    "sql_patterns": [
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+",
    ],
}

# =============================================================================
# Prompt Templates
# =============================================================================

PROMPT_TEMPLATES = {
    "image_generation": {
        "template": "High-quality UI/UX focused image of {{subject}}, designed for {{context}} interface, modern, minimal, clean layout, neutral lighting, flat background, professional product design aesthetic.",
        "recommended_parameters": {
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler": "DPM++",
            "denoise": 1.0,
        },
    },
    "video_generation": {
        "template": "Short cinematic UI animation of {{subject}}, smooth motion, subtle transitions, loopable, modern interface style, clean background, professional design motion.",
        "recommended_parameters": {
            "frames": 48,
            "fps": 8,
            "motion_strength": 0.6,
            "guidance_scale": 7.5,
        },
    },
    "model3d_generation": {
        "template": "3D object of {{subject}}, clean topology, UI-ready asset, centered, neutral lighting, optimized geometry, suitable for web rendering.",
        "recommended_parameters": {
            "detail_level": "medium",
            "texture_resolution": "1k",
            "vertex_limit": 200000,
            "polygon_count": "low-poly",
        },
    },
}

# =============================================================================
# Password Policy
# =============================================================================

PASSWORD_POLICY = {
    "min_length": 10,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special_chars": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "max_length": 128,
}

# =============================================================================
# Token Configuration
# =============================================================================

TOKEN_CONFIG = {
    "access_token": {
        "lifetime_minutes": 15,
        "usage": "API authorization",
    },
    "refresh_token": {
        "lifetime_days": 7,
        "usage": "Access token renewal",
    },
}

# =============================================================================
# Optimization Strategies
# =============================================================================

OPTIMIZATION_STRATEGIES = {
    "prompt_optimization": [
        "Encourage concise prompts (under 500 chars)",
        "Use structured templates to ensure consistency",
        "Avoid ambiguous language",
        "Include specific style descriptors",
    ],
    "model_optimization": [
        "Use quantized models where applicable (int8, fp16)",
        "Unload models from VRAM after job completion",
        "Pin model versions for reproducibility",
        "Cache frequently used models",
        "Batch similar generation requests",
    ],
    "system_optimization": [
        "Batch low-priority jobs during off-peak hours",
        "Implement intelligent queue management",
        "Use connection pooling for database",
        "Cache API responses with TTL",
        "Implement async job processing",
    ],
}
