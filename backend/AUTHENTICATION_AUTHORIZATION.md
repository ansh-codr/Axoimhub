# Component 8: Authentication & Authorization System

## Overview

This component implements a complete, production-ready authentication and authorization system for the Axiom Design Engine backend. It includes JWT token management, RBAC (Role-Based Access Control), safety guardrails, resource limits, and prompt sanitization.

## Key Features

### 1. Authentication System (JWT)

**Token Configuration:**
- **Access Tokens**: 15-minute lifetime for API authorization
- **Refresh Tokens**: 7-day lifetime for token renewal
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Payload**: User ID, role, token type, expiration, issued-at timestamps

**Password Policy:**
- Minimum 10 characters
- Maximum 128 characters
- Requires uppercase letter (A-Z)
- Requires lowercase letter (a-z)
- Requires digit (0-9)
- Requires special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Authentication Endpoints:**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/change-password` - Change password

### 2. Authorization System (RBAC)

**Roles and Permissions:**

**User Role:**
- `create_job` - Create generation jobs
- `cancel_job` - Cancel own jobs
- `retry_job` - Retry failed jobs
- `view_own_assets` - View own assets
- `download_assets` - Download assets
- `delete_assets` - Delete own assets
- `create_project` - Create projects
- `edit_project` - Edit own projects
- `delete_project` - Delete own projects

**Admin Role:**
- All user permissions plus:
- `manage_users` - Create, update, delete users
- `view_all_assets` - View all assets
- `view_all_jobs` - View all jobs
- `manage_workers` - Start, stop, configure workers
- `system_configuration` - Configure system settings
- `manage_settings` - Manage app settings

**System Role (Internal):**
- `internal_callbacks` - Accept worker callbacks
- `worker_status_updates` - Update worker status
- `execute_jobs` - Execute jobs on workers

### 3. Safety & Guardrails

**Prompt Sanitization:**
- Strips executable code patterns
- Rejects filesystem paths (prevents directory traversal)
- Rejects SQL injection patterns
- Enforces maximum prompt length (4000 characters)
- Normalizes whitespace and formatting

**Content Restrictions:**
- No identity impersonation requests
- No biometric replication requests
- No explicit/adult content
- No violence or gore
- No hate speech

**Resource Limits:**
- **Images**: Maximum 2048×2048 pixels (4.19 megapixels)
- **Videos**: Maximum 6 seconds, 48 frames, 8 FPS
- **3D Models**: Maximum 200,000 polygons
- **Files**: Maximum 512 MB

**Job Rate Limits:**
- Maximum 3 concurrent jobs per user
- Maximum 100 jobs per day per user
- Maximum 20 jobs per hour per user

### 4. Prompt Templates

**Image Generation:**
```
High-quality UI/UX focused image of {{subject}}, 
designed for {{context}} interface, modern, minimal, 
clean layout, neutral lighting, flat background, 
professional product design aesthetic.
```

Recommended parameters:
- Steps: 30
- CFG Scale: 7.5
- Sampler: DPM++

**Video Generation:**
```
Short cinematic UI animation of {{subject}}, 
smooth motion, subtle transitions, loopable, 
modern interface style, clean background, 
professional design motion.
```

Recommended parameters:
- Frames: 48
- FPS: 8
- Motion Strength: 0.6

**3D Model Generation:**
```
3D object of {{subject}}, clean topology, 
UI-ready asset, centered, neutral lighting, 
optimized geometry, suitable for web rendering.
```

Recommended parameters:
- Detail Level: medium
- Texture Resolution: 1k
- Polygon Limit: 200,000

## Implementation Details

### Core Modules

**`app/core/auth_config.py`**
- Permission definitions
- RBAC role mappings
- Safety and guardrail configurations
- Prompt templates
- Resource limits
- Password policy

**`app/core/security.py`**
- JWT token creation and validation
- Password hashing (bcrypt with 12 rounds)
- Password strength validation
- Token payload structure

**`app/core/authorization.py`**
- RBAC dependency factories
- Permission checking
- Access control helpers

**`app/utils/prompt_sanitizer.py`**
- `PromptSanitizer` class for prompt cleaning
- `PromptValidator` class for validation
- Pattern matching for dangerous content
- Whitespace normalization

**`app/utils/job_limiter.py`**
- `JobLimiter` for rate limit enforcement
- `ResourceLimiter` for resource validation
- Concurrent job checking
- Daily/hourly job counting

### Usage Examples

**Protecting Routes with Permissions:**
```python
from fastapi import APIRouter, Depends
from typing import Annotated
from app.core.auth_config import Permission
from app.core.authorization import require_permission
from app.models.user import User

router = APIRouter()

@router.post("/jobs")
async def create_job(
    user: Annotated[User, Depends(require_permission(Permission.CREATE_JOB))],
    request: JobCreateRequest,
):
    # User has CREATE_JOB permission
    ...
```

**Protecting Routes with Roles:**
```python
from app.core.dependencies import require_role
from app.models.user import UserRole

@router.post("/admin/users")
async def manage_users(
    user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    # User is admin or higher
    ...
```

**Sanitizing User Prompts:**
```python
from app.utils.prompt_sanitizer import PromptSanitizer

sanitizer = PromptSanitizer()
try:
    clean_prompt = sanitizer.sanitize(user_prompt)
except ValidationError as e:
    # Handle sanitization error
    ...
```

**Enforcing Job Limits:**
```python
from app.utils.job_limiter import JobLimiter

allowed, reason = await JobLimiter.enforce_job_limits(user_id, db)
if not allowed:
    raise ValidationError(reason)
```

**Validating Resources:**
```python
from app.utils.job_limiter import ResourceLimiter

ResourceLimiter.validate_image_resolution(width, height)
ResourceLimiter.validate_video_duration(duration_seconds)
ResourceLimiter.validate_model3d_faces(face_count)
```

## Database Considerations

**User Model Fields Required:**
- `email` (unique, indexed)
- `password_hash` (bcrypt hash)
- `role` (enum: user, admin)
- `is_active` (boolean)
- `last_login_at` (timestamp)
- `created_at` (timestamp)
- `updated_at` (timestamp)

## Environment Configuration

Required environment variables:
```env
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_HASH_ROUNDS=12
WORKER_API_KEY=<generate-secure-key>
```

## Security Best Practices

1. **Token Storage**: Access tokens should be stored in httpOnly cookies or memory
2. **Refresh Token Rotation**: Consider implementing refresh token rotation for added security
3. **CORS**: Ensure CORS is properly configured to prevent unauthorized cross-origin requests
4. **Rate Limiting**: Implement rate limiting on auth endpoints to prevent brute force attacks
5. **HTTPS**: Always use HTTPS in production
6. **Secret Management**: Use environment variables and secret management systems for sensitive configuration
7. **Password Storage**: Never log or display passwords, always use bcrypt hashing
8. **Token Expiration**: Use short-lived access tokens with longer-lived refresh tokens

## Monitoring & Logging

**Key Events to Monitor:**
- Failed login attempts
- Permission denied errors
- Unusual job creation rates
- Resource limit violations
- Prompt sanitization failures
- Token expiration and refresh events

## Future Enhancements

1. **OAuth2/OIDC Integration**: Support third-party identity providers
2. **Multi-Factor Authentication**: Implement MFA for enhanced security
3. **Session Management**: Add session tracking and management
4. **Audit Logging**: Comprehensive audit trail for all actions
5. **API Keys**: Support API key-based authentication for programmatic access
6. **Rate Limiting**: Implement distributed rate limiting with Redis
7. **RBAC Enhancement**: Dynamic permission mapping and group-based roles
8. **Prompt Filtering**: Machine learning-based content filtering
