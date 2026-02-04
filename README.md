# Axoimhub

A self-hosted, open-source AI platform for generating UI/UX-focused images, short videos, and 3D assets using local and cloud-deployed AI models.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AXIOM DESIGN ENGINE                            │
├─────────────────────────────────────────────────────────────────────────────┤

## Project Workflow (How it Works)

│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Frontend  │    │   Backend   │    │   Workers   │    │  ComfyUI    │   │
│  │  (Next.js)  │───▶│  (FastAPI)  │───▶│  (Celery)   │───▶│ Orchestrator│   │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘    └─────────────┘   │
│                            │                  │                             │
│                     ┌──────▼──────┐    ┌──────▼──────┐                      │
│                     │  PostgreSQL │    │    Redis    │                      │
│                     │  (Primary)  │    │   (Queue)   │                      │
│                     └─────────────┘    └─────────────┘                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Storage Layer (S3/MinIO/Local)              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

```

## Project Structure

```
axiom-engine/
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core config, security, dependencies
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic layer
│   │   └── utils/          # Utility functions
│   ├── migrations/         # Alembic database migrations
│   └── tests/              # Backend tests
│
├── frontend/               # Next.js frontend application
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utility libraries
│   │   ├── services/      # API client services
│   │   ├── stores/        # State management (Zustand)
│   │   └── types/         # TypeScript type definitions
│   └── public/            # Static assets
│
├── workers/               # Celery worker processes
│   ├── tasks/            # Task definitions
│   ├── handlers/         # Execution handlers (local/cloud)
│   └── utils/            # Worker utilities
│
├── orchestration/         # ComfyUI integration layer
│   ├── workflows/        # ComfyUI workflow JSON definitions
│   ├── adapters/         # Model-specific adapters
│   └── client/           # ComfyUI API client
│
├── infrastructure/        # Deployment configurations
│   ├── docker/           # Dockerfiles for each service
│   ├── compose/          # Docker Compose configurations
│   ├── kubernetes/       # Kubernetes manifests
│   └── scripts/          # Deployment and utility scripts
│
├── storage/              # Asset storage abstraction
│   ├── adapters/         # Storage backend adapters
│   └── utils/            # Storage utilities
│
├── shared/               # Shared code across services
│   ├── constants/        # Shared constants
│   ├── types/            # Shared type definitions
│   └── utils/            # Shared utilities
│
├── docs/                 # Documentation
│   ├── api/              # API documentation
│   ├── deployment/       # Deployment guides
│   └── development/      # Development guides
│
├── scripts/              # Project-level scripts
│   ├── setup.sh          # Initial setup script
│   ├── dev.sh            # Development startup
│   └── test.sh           # Test runner
│
├── .github/              # GitHub Actions workflows
│   └── workflows/
│
├── .env.example          # Environment variable template
├── docker-compose.yml    # Primary compose file
├── docker-compose.dev.yml # Development overrides
├── Makefile              # Common commands
└── pyproject.toml        # Python project configuration
```

## Directory Descriptions

### `/backend`
FastAPI-based REST API server handling authentication, job management, and asset serving. Follows clean architecture with separation between routes, services, and data access.

### `/frontend`
Next.js 14+ application with App Router, TypeScript, and Tailwind CSS. Provides UI for prompt input, real-time job monitoring, and asset preview/download.

### `/workers`
Celery workers for async job processing. Supports both local GPU execution and cloud provider fallback. Each worker is isolated and stateless.

### `/orchestration`
Integration layer for ComfyUI. Contains workflow definitions, parameter mappers, and the API client for triggering inference pipelines.

### `/infrastructure`
All deployment configurations including Docker, Docker Compose, and Kubernetes manifests. Supports local development, staging, and production environments.

### `/storage`
Abstraction layer for asset storage. Supports local filesystem, S3-compatible storage (MinIO), and cloud providers.

### `/shared`
Cross-service shared code including constants, types, and utilities. Ensures consistency across Python and TypeScript codebases.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/axiom-engine.git
cd axiom-engine
cp .env.example .env

# Start all services (development)
make dev

# Or with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Requirements

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- CUDA-capable GPU (12GB+ VRAM recommended)

## Local GPU Setup (RTX 3060 8GB)

This repo is pre-wired for SDXL (image), SVD (video), and TripoSR (3D) via ComfyUI.

### 1) Prepare the test laptop

- Install Docker Desktop.
- Install NVIDIA drivers and NVIDIA Container Toolkit.

### 2) Clone the repo

git clone <your-repo-url>
cd axiom-engine

### 3) Install ComfyUI custom nodes

Run:
scripts/setup-comfyui-custom-nodes.sh

### 4) Download model files

Run:
scripts/setup-comfyui-models.sh

Then place these files:
- models/checkpoints/sd_xl_base_1.0.safetensors
- models/checkpoints/svd_xt_1_1.safetensors

### 5) Start GPU services

docker compose --profile gpu up --build

### 6) Verify

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/api/v1/health
- ComfyUI: http://localhost:8188

### Recommended 8GB settings

- Image: 768x768, steps 30
- Video: 576x320, 16–24 frames, fps 8–12

If you want additional models or higher resolutions, tell me the GPU VRAM and I’ll add the workflows.

## License

MIT License - See LICENSE file for details.
