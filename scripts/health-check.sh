#!/bin/bash
# =============================================================================
# Axiom Design Engine - Health Check Script
# Verify all services are running correctly
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
COMFYUI_URL="${COMFYUI_URL:-http://localhost:8188}"
TIMEOUT=5

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

check_endpoint() {
    local name=$1
    local url=$2
    local expected=${3:-200}
    
    printf "  %-20s" "$name"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$url" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} ($HTTP_CODE)"
        return 0
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "${RED}✗${NC} (connection failed)"
        return 1
    else
        echo -e "${YELLOW}!${NC} ($HTTP_CODE, expected $expected)"
        return 1
    fi
}

check_container() {
    local name=$1
    
    printf "  %-20s" "$name"
    
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        STATUS=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null)
        if [ "$STATUS" = "running" ]; then
            echo -e "${GREEN}✓${NC} (running)"
            return 0
        else
            echo -e "${YELLOW}!${NC} ($STATUS)"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} (not found)"
        return 1
    fi
}

check_postgres() {
    printf "  %-20s" "postgres"
    
    if docker exec axiom-db pg_isready -U axiom -d axiom_engine &> /dev/null; then
        echo -e "${GREEN}✓${NC} (ready)"
        return 0
    else
        echo -e "${RED}✗${NC} (not ready)"
        return 1
    fi
}

check_redis() {
    printf "  %-20s" "redis"
    
    if docker exec axiom-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✓${NC} (ready)"
        return 0
    else
        echo -e "${RED}✗${NC} (not ready)"
        return 1
    fi
}

check_gpu() {
    printf "  %-20s" "gpu"
    
    if docker exec axiom-worker-gpu python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        GPU_NAME=$(docker exec axiom-worker-gpu python -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
        echo -e "${GREEN}✓${NC} ($GPU_NAME)"
        return 0
    else
        echo -e "${YELLOW}!${NC} (not available or container not running)"
        return 1
    fi
}

run_smoke_test() {
    log_info "Running smoke test..."
    
    # Test API health
    HEALTH=$(curl -s "${BACKEND_URL}/api/v1/health" 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Test database connection via API
    # (Assuming there's a ready endpoint that checks DB)
    READY=$(curl -s "${BACKEND_URL}/api/v1/ready" 2>/dev/null)
    if echo "$READY" | grep -q "ready"; then
        log_success "Database connection check passed"
    else
        log_warn "Database connection check inconclusive"
    fi
}

main() {
    echo "============================================="
    echo "  Axiom Design Engine - Health Check"
    echo "============================================="
    echo ""
    
    FAILED=0
    
    log_info "Checking containers..."
    check_container "axiom-db" || ((FAILED++))
    check_container "axiom-redis" || ((FAILED++))
    check_container "axiom-backend" || ((FAILED++))
    check_container "axiom-frontend" || ((FAILED++))
    check_container "axiom-worker-cpu" || ((FAILED++))
    check_container "axiom-worker-gpu" || true  # GPU is optional
    check_container "axiom-comfyui" || true     # ComfyUI is optional
    echo ""
    
    log_info "Checking services..."
    check_postgres || ((FAILED++))
    check_redis || ((FAILED++))
    echo ""
    
    log_info "Checking endpoints..."
    check_endpoint "backend" "${BACKEND_URL}/api/v1/health" || ((FAILED++))
    check_endpoint "frontend" "${FRONTEND_URL}" || ((FAILED++))
    check_endpoint "api-docs" "${BACKEND_URL}/docs" || ((FAILED++))
    check_endpoint "comfyui" "${COMFYUI_URL}/system_stats" || true  # Optional
    echo ""
    
    log_info "Checking GPU..."
    check_gpu || true  # Optional
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo ""
        log_success "All health checks passed!"
        exit 0
    else
        echo ""
        log_error "$FAILED health check(s) failed"
        exit 1
    fi
}

main "$@"
