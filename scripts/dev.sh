#!/bin/bash
# =============================================================================
# AXIOM DESIGN ENGINE - Development Startup Script
# =============================================================================
set -e

echo "🚀 Starting Axiom Design Engine in development mode..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Start infrastructure services
echo ""
echo "📦 Starting infrastructure services (PostgreSQL, Redis)..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
until docker-compose exec -T postgres pg_isready -U $POSTGRES_USER > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✓ PostgreSQL is ready"

# Check Redis
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo "✓ Redis is ready"

# Run database migrations
echo ""
echo "🗃️  Running database migrations..."
cd backend && alembic upgrade head && cd ..

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml stop postgres redis
    echo "✓ Services stopped"
}
trap cleanup EXIT

# Start services in background
echo ""
echo "🌐 Starting application services..."

# Backend API
echo "  Starting backend API on http://localhost:8000..."
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Celery Worker
echo "  Starting Celery worker..."
cd workers && celery -A tasks worker --loglevel=info --concurrency=2 &
WORKER_PID=$!
cd ..

# Frontend
echo "  Starting frontend on http://localhost:3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait
