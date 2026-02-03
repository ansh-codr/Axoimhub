"""
Axiom Design Engine - API v1 Router
Combines all v1 API routes
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.assets import router as assets_router
from app.api.v1.projects import router as projects_router
from app.api.v1.templates import router as templates_router
from app.api.v1.internal import router as internal_router

# Create main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(jobs_router)
api_router.include_router(assets_router)
api_router.include_router(templates_router)
api_router.include_router(internal_router)

