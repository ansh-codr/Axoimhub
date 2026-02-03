#!/bin/bash
# =============================================================================
# Axiom Design Engine - Development Setup Script
# Quick start for local development
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_docker() {
    log_info "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed."
    fi
    
    log_success "Docker is ready"
}

check_nvidia() {
    log_info "Checking NVIDIA GPU support..."
    
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
        
        if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            log_success "NVIDIA GPU support is available"
            GPU_AVAILABLE=true
        else
            log_warn "NVIDIA container toolkit not configured. GPU features will be disabled."
            GPU_AVAILABLE=false
        fi
    else
        log_warn "NVIDIA GPU not detected. Running in CPU-only mode."
        GPU_AVAILABLE=false
    fi
}

setup_env() {
    log_info "Setting up environment..."
    
    cd "$PROJECT_ROOT"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Created .env from .env.example"
            
            # Generate secrets
            JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p)
            WORKER_API_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p)
            
            # Update .env with generated secrets
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env
                sed -i '' "s/WORKER_API_KEY=.*/WORKER_API_KEY=${WORKER_API_KEY}/" .env
            else
                sed -i "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env
                sed -i "s/WORKER_API_KEY=.*/WORKER_API_KEY=${WORKER_API_KEY}/" .env
            fi
            
            log_success "Generated secure secrets in .env"
        else
            log_error ".env.example not found"
        fi
    else
        log_info ".env already exists, skipping"
    fi
}

create_directories() {
    log_info "Creating data directories..."
    
    mkdir -p "${PROJECT_ROOT}/data/axiom-storage"
    mkdir -p "${PROJECT_ROOT}/data/models"
    mkdir -p "${PROJECT_ROOT}/data/postgres"
    mkdir -p "${PROJECT_ROOT}/data/redis"
    
    log_success "Data directories created"
}

start_services() {
    log_info "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    # Determine compose command
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Start base services first
    $COMPOSE_CMD up -d db redis
    
    log_info "Waiting for database to be ready..."
    sleep 5
    
    # Start application services
    $COMPOSE_CMD up -d backend frontend worker-cpu
    
    # Start GPU services if available
    if [ "${GPU_AVAILABLE:-false}" = true ]; then
        log_info "Starting GPU services..."
        $COMPOSE_CMD --profile gpu up -d worker-gpu comfyui
    fi
    
    log_success "Services started"
}

show_status() {
    echo ""
    echo "============================================="
    echo "  Axiom Design Engine - Development Ready"
    echo "============================================="
    echo ""
    log_info "Services:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    
    if [ "${GPU_AVAILABLE:-false}" = true ]; then
        echo "  ComfyUI:   http://localhost:8188"
    fi
    
    echo ""
    log_info "Development tools:"
    echo "  Adminer:   http://localhost:8080 (database)"
    echo "  Redis UI:  http://localhost:8081"
    echo "  Mailhog:   http://localhost:8025 (emails)"
    echo ""
    log_info "To view logs:"
    echo "  docker compose logs -f [service]"
    echo ""
    log_info "To stop:"
    echo "  docker compose down"
    echo ""
}

main() {
    echo "============================================="
    echo "  Axiom Design Engine - Development Setup"
    echo "============================================="
    echo ""
    
    check_docker
    check_nvidia
    setup_env
    create_directories
    start_services
    show_status
}

main "$@"
