# =============================================================================
# Axiom Design Engine - GPU Worker Dockerfile
# Celery worker with CUDA support for AI inference
# =============================================================================

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS base

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Labels
LABEL org.opencontainers.image.title="Axiom Design Engine - GPU Worker"
LABEL org.opencontainers.image.description="Celery worker with CUDA for AI generation"
LABEL org.opencontainers.image.vendor="Axiom"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create symlinks for python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create non-root user
RUN groupadd --gid 1000 axiom && \
    useradd --uid 1000 --gid axiom --shell /bin/bash --create-home axiom

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM base AS dependencies

WORKDIR /build

# Install PyTorch with CUDA support first
RUN pip install --no-cache-dir \
    torch==2.1.2+cu121 \
    torchvision==0.16.2+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Install AI/ML dependencies
RUN pip install --no-cache-dir \
    transformers>=4.36.2 \
    diffusers>=0.25.0 \
    accelerate>=0.25.0 \
    safetensors>=0.4.1 \
    xformers>=0.0.23

# Install worker dependencies
COPY workers/pyproject.toml ./
RUN pip install --no-cache-dir \
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
    opencv-python-headless>=4.9.0 \
    numpy>=1.26.3 \
    trimesh>=4.0.0

# =============================================================================
# Production Image
# =============================================================================
FROM base AS production

# Copy virtual environment
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy worker code
COPY --chown=axiom:axiom workers ./workers
COPY --chown=axiom:axiom orchestration ./orchestration

# Create data directories
RUN mkdir -p /data/axiom-storage /data/models && \
    chown -R axiom:axiom /data

# Switch to non-root user
USER axiom

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    CUDA_VISIBLE_DEVICES=0 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Health check - verify GPU access
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import torch; assert torch.cuda.is_available()" || exit 1

# Default: start image queue worker (can be overridden)
CMD ["celery", "-A", "workers.celery_app", "worker", \
     "--loglevel=INFO", \
     "-Q", "queue_image,queue_video,queue_3d", \
     "-c", "1", \
     "--max-tasks-per-child=50"]
