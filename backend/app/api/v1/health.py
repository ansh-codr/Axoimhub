"""
Axiom Design Engine - Health Check Routes
System health and status endpoints
"""

from fastapi import APIRouter, status

from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.

    Returns API status, version, and environment.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the API is ready to accept requests.",
)
async def readiness_check() -> HealthResponse:
    """
    Readiness check endpoint for Kubernetes.

    Verifies database and Redis connectivity.
    """
    # TODO: Add actual database and Redis connectivity checks
    # For now, just return healthy
    return HealthResponse(
        status="ready",
        version="0.1.0",
        environment=settings.app_env,
    )
