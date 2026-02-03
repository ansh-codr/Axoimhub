#!/bin/bash
# =============================================================================
# Axiom Design Engine - Deployment Script
# Deploy to Kubernetes using Kustomize
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-staging}"
DRY_RUN="${DRY_RUN:-false}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/../k8s"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  staging     Deploy to staging environment (default)"
    echo "  production  Deploy to production environment"
    echo ""
    echo "Options:"
    echo "  DRY_RUN=true  Preview changes without applying"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  DRY_RUN=true $0 production"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warn "kustomize not found, using kubectl kustomize"
        USE_KUBECTL_KUSTOMIZE=true
    else
        USE_KUBECTL_KUSTOMIZE=false
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
    fi
    
    log_success "Prerequisites check passed"
}

validate_environment() {
    case "$ENVIRONMENT" in
        staging|production)
            log_info "Environment: $ENVIRONMENT"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT. Use 'staging' or 'production'"
            ;;
    esac
    
    OVERLAY_DIR="${K8S_DIR}/overlays/${ENVIRONMENT}"
    
    if [ ! -d "$OVERLAY_DIR" ]; then
        log_error "Overlay directory not found: $OVERLAY_DIR"
    fi
}

build_manifests() {
    log_info "Building Kubernetes manifests..."
    
    if [ "$USE_KUBECTL_KUSTOMIZE" = true ]; then
        kubectl kustomize "$OVERLAY_DIR" > /tmp/axiom-manifests.yaml
    else
        kustomize build "$OVERLAY_DIR" > /tmp/axiom-manifests.yaml
    fi
    
    log_success "Manifests built successfully"
}

deploy() {
    log_info "Deploying to $ENVIRONMENT..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_warn "DRY RUN - showing diff only"
        kubectl diff -f /tmp/axiom-manifests.yaml || true
    else
        kubectl apply -f /tmp/axiom-manifests.yaml
        
        log_info "Waiting for deployments to be ready..."
        
        NAMESPACE="ai-platform"
        if [ "$ENVIRONMENT" = "staging" ]; then
            NAMESPACE="ai-platform-staging"
        fi
        
        # Wait for deployments
        kubectl -n "$NAMESPACE" rollout status deployment/axiom-backend --timeout=300s || true
        kubectl -n "$NAMESPACE" rollout status deployment/axiom-frontend --timeout=300s || true
        kubectl -n "$NAMESPACE" rollout status deployment/axiom-worker-cpu --timeout=300s || true
        
        log_success "Deployment completed successfully"
    fi
}

show_status() {
    NAMESPACE="ai-platform"
    if [ "$ENVIRONMENT" = "staging" ]; then
        NAMESPACE="ai-platform-staging"
    fi
    
    log_info "Deployment status:"
    echo ""
    kubectl -n "$NAMESPACE" get pods
    echo ""
    kubectl -n "$NAMESPACE" get services
    echo ""
    kubectl -n "$NAMESPACE" get ingress
}

cleanup() {
    rm -f /tmp/axiom-manifests.yaml
}

# Main
main() {
    trap cleanup EXIT
    
    echo "============================================="
    echo "  Axiom Design Engine - Kubernetes Deploy"
    echo "============================================="
    echo ""
    
    check_prerequisites
    validate_environment
    build_manifests
    deploy
    show_status
    
    echo ""
    log_success "Done!"
}

main "$@"
