#!/bin/bash
# =============================================================================
# Axiom Design Engine - Docker Build Script
# Build and push Docker images
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY="${REGISTRY:-}"
TAG="${TAG:-latest}"
PUSH="${PUSH:-false}"
PLATFORM="${PLATFORM:-linux/amd64}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."

# Services to build
SERVICES=("backend" "frontend" "worker-gpu" "worker-cpu" "comfyui")

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

usage() {
    echo "Usage: $0 [options] [services...]"
    echo ""
    echo "Options:"
    echo "  -r, --registry    Container registry (e.g., ghcr.io/username)"
    echo "  -t, --tag         Image tag (default: latest)"
    echo "  -p, --push        Push images after building"
    echo "  --platform        Build platform (default: linux/amd64)"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Services: backend, frontend, worker-gpu, worker-cpu, comfyui, all"
    echo ""
    echo "Examples:"
    echo "  $0 backend frontend"
    echo "  $0 -r ghcr.io/myorg -t v1.0.0 -p all"
}

parse_args() {
    SELECTED_SERVICES=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            -p|--push)
                PUSH="true"
                shift
                ;;
            --platform)
                PLATFORM="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            all)
                SELECTED_SERVICES=("${SERVICES[@]}")
                shift
                ;;
            *)
                if [[ " ${SERVICES[*]} " =~ " $1 " ]]; then
                    SELECTED_SERVICES+=("$1")
                else
                    log_error "Unknown service: $1"
                fi
                shift
                ;;
        esac
    done
    
    if [ ${#SELECTED_SERVICES[@]} -eq 0 ]; then
        SELECTED_SERVICES=("${SERVICES[@]}")
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
    fi
}

build_image() {
    local service=$1
    local dockerfile="docker/${service}/Dockerfile"
    local image_name="axiom-engine/${service}"
    
    if [ -n "$REGISTRY" ]; then
        image_name="${REGISTRY}/${image_name}"
    fi
    
    log_info "Building ${service}..."
    
    if [ ! -f "${PROJECT_ROOT}/${dockerfile}" ]; then
        log_warn "Dockerfile not found: ${dockerfile}, skipping"
        return
    fi
    
    docker build \
        --platform "$PLATFORM" \
        -t "${image_name}:${TAG}" \
        -t "${image_name}:latest" \
        -f "${PROJECT_ROOT}/${dockerfile}" \
        "$PROJECT_ROOT"
    
    log_success "Built ${image_name}:${TAG}"
    
    if [ "$PUSH" = "true" ]; then
        log_info "Pushing ${image_name}:${TAG}..."
        docker push "${image_name}:${TAG}"
        docker push "${image_name}:latest"
        log_success "Pushed ${image_name}:${TAG}"
    fi
}

main() {
    echo "============================================="
    echo "  Axiom Design Engine - Docker Build"
    echo "============================================="
    echo ""
    
    parse_args "$@"
    check_docker
    
    log_info "Building services: ${SELECTED_SERVICES[*]}"
    log_info "Tag: ${TAG}"
    log_info "Platform: ${PLATFORM}"
    [ -n "$REGISTRY" ] && log_info "Registry: ${REGISTRY}"
    [ "$PUSH" = "true" ] && log_info "Push: enabled"
    echo ""
    
    for service in "${SELECTED_SERVICES[@]}"; do
        build_image "$service"
        echo ""
    done
    
    log_success "Build complete!"
}

main "$@"
