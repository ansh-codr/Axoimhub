# =============================================================================
# Axiom Design Engine - CPU Worker Dockerfile
# Celery worker for CPU-only tasks and callbacks
# =============================================================================

FROM python:3.11-slim AS builder

# Build arguments
ARG PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
WORKDIR /build
COPY workers/pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install \
    celery[redis]>=5.3.6 \
    redis>=5.0.1 \
    kombu>=5.3.4 \
    httpx>=0.26.0 \
    websockets>=12.0 \
    aiofiles>=23.2.1 \
    boto3>=1.34.0 \
    pydantic>=2.5.3 \
    pydantic-settings>=2.1.0 \
    orjson>=3.9.10 \
    prometheus-client>=0.19.0 \
    pillow>=10.2.0 \
    numpy>=1.26.3

# =============================================================================
# Production Image
# =============================================================================
FROM python:3.11-slim AS production

# Labels
LABEL org.opencontainers.image.title="Axiom Design Engine - CPU Worker"
LABEL org.opencontainers.image.description="Celery worker for callbacks and CPU tasks"
LABEL org.opencontainers.image.vendor="Axiom"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 axiom && \
    useradd --uid 1000 --gid axiom --shell /bin/bash --create-home axiom

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy worker code
COPY --chown=axiom:axiom workers ./workers
COPY --chown=axiom:axiom orchestration ./orchestration

# Create data directories
RUN mkdir -p /data/axiom-storage && chown -R axiom:axiom /data

# Switch to non-root user
USER axiom

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A workers.celery_app inspect ping || exit 1

# Start callback queue worker
CMD ["celery", "-A", "workers.celery_app", "worker", \
     "--loglevel=INFO", \
     "-Q", "queue_callbacks", \
     "-c", "4"]
