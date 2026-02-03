# =============================================================================
# AXIOM DESIGN ENGINE - Makefile
# =============================================================================

.PHONY: help install dev build test lint format clean docker-up docker-down migrate

# Default target
help:
	@echo "Axiom Design Engine - Available Commands"
	@echo "========================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install all dependencies"
	@echo "  make install-backend - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services in development mode"
	@echo "  make dev-backend    - Start backend only"
	@echo "  make dev-frontend   - Start frontend only"
	@echo "  make dev-worker     - Start Celery worker"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Start all services with Docker Compose"
	@echo "  make docker-down    - Stop all Docker services"
	@echo "  make docker-build   - Build all Docker images"
	@echo "  make docker-logs    - View Docker container logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create a new migration"
	@echo "  make db-reset       - Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make test-coverage  - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run all linters"
	@echo "  make format         - Format all code"
	@echo "  make typecheck      - Run type checking"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make clean-docker   - Remove Docker volumes and images"

# =============================================================================
# Installation
# =============================================================================

install: install-backend install-frontend
	@echo "All dependencies installed successfully!"

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# =============================================================================
# Development
# =============================================================================

dev:
	@echo "Starting all services in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
	@sleep 3
	$(MAKE) -j3 dev-backend dev-frontend dev-worker

dev-backend:
	@echo "Starting backend server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend server..."
	cd frontend && npm run dev

dev-worker:
	@echo "Starting Celery worker..."
	cd workers && celery -A tasks worker --loglevel=info --concurrency=2

dev-comfyui:
	@echo "Starting ComfyUI..."
	cd orchestration && python -m comfyui.main --listen 0.0.0.0 --port 8188

# =============================================================================
# Docker
# =============================================================================

docker-up:
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d

docker-up-dev:
	@echo "Starting services in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-down:
	@echo "Stopping all Docker services..."
	docker-compose down

docker-build:
	@echo "Building all Docker images..."
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-shell-backend:
	docker-compose exec backend /bin/bash

docker-shell-worker:
	docker-compose exec worker /bin/bash

# =============================================================================
# Database
# =============================================================================

migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	cd backend && alembic revision --autogenerate -m "$$name"

migrate-downgrade:
	@echo "Rolling back last migration..."
	cd backend && alembic downgrade -1

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cd backend && alembic downgrade base && alembic upgrade head; \
	fi

# =============================================================================
# Testing
# =============================================================================

test: test-backend test-frontend
	@echo "All tests completed!"

test-backend:
	@echo "Running backend tests..."
	cd backend && pytest -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

test-e2e:
	@echo "Running end-to-end tests..."
	cd frontend && npm run test:e2e

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-backend lint-frontend
	@echo "Linting completed!"

lint-backend:
	@echo "Linting backend code..."
	cd backend && ruff check app tests
	cd backend && mypy app

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

format: format-backend format-frontend
	@echo "Formatting completed!"

format-backend:
	@echo "Formatting backend code..."
	cd backend && ruff format app tests
	cd backend && ruff check --fix app tests

format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format

typecheck:
	@echo "Running type checks..."
	cd backend && mypy app
	cd frontend && npm run typecheck

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf frontend/coverage 2>/dev/null || true

clean-docker:
	@echo "Removing Docker volumes and images..."
	docker-compose down -v --rmi local

# =============================================================================
# Utilities
# =============================================================================

shell-backend:
	cd backend && python -c "from app.core.config import settings; import IPython; IPython.embed()"

generate-secret:
	@openssl rand -hex 32

check-gpu:
	@python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}'); print(f'Current device: {torch.cuda.current_device() if torch.cuda.is_available() else \"N/A\"}')"
