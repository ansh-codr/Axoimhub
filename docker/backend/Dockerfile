# =============================================================================
# Axiom Design Engine - Backend Dockerfile
# FastAPI application server
# =============================================================================

FROM python:3.11-slim AS builder

# Build arguments
ARG PIP_NO_CACHE_DIR=1
ARG PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
WORKDIR /build
COPY backend/pyproject.toml backend/requirements.txt* ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . || pip install \
    fastapi[all]>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    sqlalchemy[asyncio]>=2.0.25 \
    asyncpg>=0.29.0 \
    alembic>=1.13.1 \
    pydantic>=2.5.3 \
    pydantic-settings>=2.1.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    redis>=5.0.1 \
    httpx>=0.26.0 \
    python-multipart>=0.0.6 \
    orjson>=3.9.10 \
    boto3>=1.34.0

# =============================================================================
# Production Image
# =============================================================================
FROM python:3.11-slim AS production

# Labels
LABEL org.opencontainers.image.title="Axiom Design Engine - Backend"
LABEL org.opencontainers.image.description="FastAPI backend for AI generation platform"
LABEL org.opencontainers.image.vendor="Axiom"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 axiom && \
    useradd --uid 1000 --gid axiom --shell /bin/bash --create-home axiom

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=axiom:axiom backend/app ./app
COPY --chown=axiom:axiom backend/alembic.ini ./
COPY --chown=axiom:axiom backend/migrations ./migrations

# Create data directories
RUN mkdir -p /data/axiom-storage && chown -R axiom:axiom /data

# Switch to non-root user
USER axiom

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    APP_ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
