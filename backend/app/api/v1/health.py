"""
Axiom Design Engine - Health Check Routes
System health and status endpoints with active DB and Redis connectivity checks
"""

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.core.redis import check_redis_health
from app.schemas.common import HealthResponse

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


async def perform_connectivity_checks(db: AsyncSession) -> tuple[bool, dict[str, str]]:
    """Perform real connectivity checks on PostgreSQL and Redis."""
    details: dict[str, str] = {}
    is_healthy = True

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        details["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        details["database"] = f"error: {str(e)}"
        is_healthy = False

    # Redis check
    try:
        redis_ok = await check_redis_health()
        if redis_ok:
            details["redis"] = "ok"
        else:
            details["redis"] = "error: ping failed"
            is_healthy = False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        details["redis"] = f"error: {str(e)}"
        is_healthy = False

    return is_healthy, details


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API and dependent services (DB, Redis) are healthy.",
    responses={
        503: {
            "model": HealthResponse,
            "description": "One or more dependent services are unhealthy",
        }
    },
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Active health check endpoint.
    Verifies API, PostgreSQL, and Redis connectivity.
    Returns 503 if any dependency fails.
    """
    is_healthy, details = await perform_connectivity_checks(db)

    payload = {
        "status": "healthy" if is_healthy else "unhealthy",
        "version": "0.1.0",
        "environment": settings.app_env,
        "database": details.get("database"),
        "redis": details.get("redis"),
    }

    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload,
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=payload,
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the API is ready to accept requests (DB and Redis healthy).",
    responses={
        503: {
            "model": HealthResponse,
            "description": "Service not ready",
        }
    },
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Readiness check endpoint for Kubernetes / orchestration.
    Verifies database and Redis connectivity. Returns 503 if not ready.
    """
    is_healthy, details = await perform_connectivity_checks(db)

    payload = {
        "status": "ready" if is_healthy else "not_ready",
        "version": "0.1.0",
        "environment": settings.app_env,
        "database": details.get("database"),
        "redis": details.get("redis"),
    }

    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload,
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=payload,
    )
