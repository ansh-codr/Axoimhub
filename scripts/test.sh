#!/bin/bash
# =============================================================================
# AXIOM DESIGN ENGINE - Test Runner Script
# =============================================================================
set -e

echo "🧪 Axiom Design Engine - Test Runner"
echo "====================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Parse arguments
RUN_BACKEND=false
RUN_FRONTEND=false
RUN_COVERAGE=false
RUN_E2E=false

if [ $# -eq 0 ]; then
    RUN_BACKEND=true
    RUN_FRONTEND=true
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend|-b)
            RUN_BACKEND=true
            shift
            ;;
        --frontend|-f)
            RUN_FRONTEND=true
            shift
            ;;
        --coverage|-c)
            RUN_COVERAGE=true
            shift
            ;;
        --e2e|-e)
            RUN_E2E=true
            shift
            ;;
        --all|-a)
            RUN_BACKEND=true
            RUN_FRONTEND=true
            RUN_E2E=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--backend|-b] [--frontend|-f] [--coverage|-c] [--e2e|-e] [--all|-a]"
            exit 1
            ;;
    esac
done

EXIT_CODE=0

# Run backend tests
if [ "$RUN_BACKEND" = true ]; then
    echo ""
    echo "🐍 Running backend tests..."
    cd backend
    
    if [ "$RUN_COVERAGE" = true ]; then
        pytest --cov=app --cov-report=html --cov-report=term-missing -v || EXIT_CODE=1
    else
        pytest -v || EXIT_CODE=1
    fi
    
    cd ..
fi

# Run frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    echo ""
    echo "⚛️  Running frontend tests..."
    cd frontend
    
    npm test -- --run || EXIT_CODE=1
    
    cd ..
fi

# Run e2e tests
if [ "$RUN_E2E" = true ]; then
    echo ""
    echo "🎭 Running end-to-end tests..."
    cd frontend
    
    npm run test:e2e || EXIT_CODE=1
    
    cd ..
fi

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
fi

exit $EXIT_CODE
