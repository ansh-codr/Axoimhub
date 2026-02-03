# =============================================================================
# Axiom Design Engine - ComfyUI Dockerfile
# ComfyUI server for AI workflow execution
# =============================================================================

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create non-root user
RUN groupadd --gid 1000 comfyui && \
    useradd --uid 1000 --gid comfyui --shell /bin/bash --create-home comfyui

# Create directories
RUN mkdir -p /app /data/models /data/output && \
    chown -R comfyui:comfyui /app /data

USER comfyui
WORKDIR /app

# Create virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install PyTorch
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    torch==2.1.2+cu121 \
    torchvision==0.16.2+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI

WORKDIR /app/ComfyUI

# Install ComfyUI requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install additional custom nodes dependencies
RUN pip install --no-cache-dir \
    opencv-python-headless \
    imageio \
    imageio-ffmpeg

# Environment
ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Expose port
EXPOSE 8188

# Volume mounts
VOLUME ["/data/models", "/data/output", "/app/ComfyUI/custom_nodes"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8188/system_stats || exit 1

# Start ComfyUI in headless mode
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--preview-method", "auto"]
