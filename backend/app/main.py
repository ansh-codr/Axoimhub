"""
Axiom Design Engine - FastAPI Application Entry Point
Main application setup with middleware, exception handlers, and lifecycle management
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AxiomException
from app.core.logging import get_logger, setup_logging
from app.db.session import close_db, init_db
from app.schemas.common import ErrorResponse

# Setup logging before anything else
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting Axiom Design Engine",
        extra={
            "environment": settings.app_env,
            "debug": settings.debug,
        },
    )

    # Initialize database connection
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Axiom Design Engine")
    await close_db()
    logger.info("Database connection closed")


def create_application() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Self-hosted AI platform for UI/UX asset generation",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(AxiomException)
    async def axiom_exception_handler(
        request: Request, exc: AxiomException
    ) -> ORJSONResponse:
        """Handle all Axiom-specific exceptions."""
        logger.warning(
            f"AxiomException: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error_code,
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": list(error["loc"]),
                    "msg": error["msg"],
                    "type": error["type"],
                }
            )

        logger.warning(
            "Validation error",
            extra={
                "path": request.url.path,
                "errors": errors,
            },
        )

        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": errors},
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> ORJSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={"path": request.url.path},
        )

        # Don't expose internal errors in production
        message = (
            str(exc)
            if settings.is_development
            else "An unexpected error occurred"
        )

        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                error_code="INTERNAL_ERROR",
                message=message,
                details={},
            ).model_dump(),
        )


# Create application instance
app = create_application()


# Root endpoint
@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": f"{settings.api_v1_prefix}/docs" if settings.is_development else "disabled",
        "health": f"{settings.api_v1_prefix}/health",
    }
