# Project Workflow

This document explains the end-to-end workflow so new contributors can quickly understand how requests move through the system and where responsibilities live.

## 1) High-Level Flow

1. **User interacts with the Frontend (Next.js).**
2. **Frontend calls Backend (FastAPI) APIs.**
3. **Backend validates, persists, and enqueues jobs.**
4. **Workers (Celery) pick up jobs from Redis.**
5. **Workers call the Orchestration layer (ComfyUI).**
6. **Outputs are stored and indexed.**
7. **Frontend polls/streams status and shows results.**

## 2) Request-to-Result Lifecycle

### A) Create Job
- **Frontend** sends a job request (prompt + settings) to **Backend**.
- **Backend**:
  - Validates input and auth.
  - Writes a **Job** record to **PostgreSQL**.
  - Pushes a task into **Redis** (Celery queue).
  - Returns the job id to the frontend.

### B) Execute Job
- **Celery Workers** consume jobs from **Redis**.
- Worker chooses the correct execution path:
  - CPU or GPU worker based on job type and availability.
  - Local or cloud execution depending on configuration.
- Worker calls **Orchestration** to:
  - Select the ComfyUI workflow JSON.
  - Map user parameters to workflow nodes.
  - Trigger the ComfyUI run and track progress.

### C) Store Results
- Outputs (images/videos/3D assets) are written through the **Storage** layer to:
  - Local filesystem, **or**
  - S3-compatible storage (e.g., MinIO).
- **Backend** updates the **Job** record with status and asset metadata.

### D) Deliver Results
- **Frontend** polls the **Backend** for status or subscribes to updates.
- Once complete, assets are shown for preview/download.

## 3) Core Components & Responsibilities

- **Frontend (Next.js)**
  - UI/UX, job submission, status updates, asset viewing.

- **Backend (FastAPI)**
  - Auth, validation, persistence, API orchestration.

- **Workers (Celery)**
  - Asynchronous execution of compute-heavy tasks.

- **Orchestration (ComfyUI Integration)**
  - Workflow mapping and inference pipeline execution.

- **Storage Layer**
  - Uniform interface over local/S3/MinIO backends.

- **PostgreSQL**
  - Source of truth for users, jobs, metadata.

- **Redis**
  - Task queue + short-lived state.

## 4) Job Status Model (Typical)

- **Queued** → **Running** → **Succeeded**
- **Queued** → **Running** → **Failed**
- **Queued** → **Canceled**

## 5) Local Development Flow

1. Run `make dev` or Docker Compose.
2. Frontend at `http://localhost:3000`.
3. Backend at `http://localhost:8000`.
4. ComfyUI at `http://localhost:8188` (if enabled).
5. Submit a job from the UI and observe status changes.

## 6) Where to Look for Changes

- **API routes**: backend/app/api
- **Business logic**: backend/app/services
- **Models/DB**: backend/app/models + backend/migrations
- **Workers**: workers/tasks + workers/handlers
- **ComfyUI mapping**: orchestration/adapters + orchestration/workflows
- **Frontend calls**: frontend/src/services
- **Storage backends**: storage/adapters

## 7) Common Extension Points

- Add a new model or pipeline:
  - Add a ComfyUI workflow in `orchestration/workflows`.
  - Add adapter mapping in `orchestration/adapters`.
  - Add new worker task if required.

- Add new asset storage:
  - Implement a storage adapter in `storage/adapters`.

- Add new UI feature:
  - Extend components in `frontend/src/components` and API calls in `frontend/src/services`.
