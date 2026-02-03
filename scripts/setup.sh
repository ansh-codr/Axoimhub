#!/bin/bash
# =============================================================================
# AXIOM DESIGN ENGINE - Initial Setup Script
# =============================================================================
set -e

echo "🚀 Axiom Design Engine - Initial Setup"
echo "======================================="

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Python $PYTHON_VERSION found"
    
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
        echo "⚠️  Warning: Python 3.11+ is recommended"
    fi
else
    echo "✗ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    echo "✓ Node.js v$NODE_VERSION found"
    
    if [[ $NODE_VERSION -lt 20 ]]; then
        echo "⚠️  Warning: Node.js 20+ is recommended"
    fi
else
    echo "✗ Node.js not found. Please install Node.js 20+"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
else
    echo "⚠️  Docker not found. Docker is required for full deployment"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "✓ Docker Compose found"
else
    echo "⚠️  Docker Compose not found"
fi

# Create virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
cd backend
pip install -e ".[dev]" --quiet
cd ..

# Install worker dependencies
echo ""
echo "📦 Installing worker dependencies..."
cd workers
pip install -e ".[dev]" --quiet
cd ..

# Install orchestration dependencies
echo ""
echo "📦 Installing orchestration dependencies..."
cd orchestration
pip install -e . --quiet
cd ..

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

# Copy environment file
echo ""
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "⚠️  Please edit .env and set your configuration values"
else
    echo "✓ .env file already exists"
fi

# Generate secret key
echo ""
echo "🔐 Generating JWT secret key..."
JWT_SECRET=$(openssl rand -hex 32)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/your-256-bit-secret-key-here/$JWT_SECRET/" .env
else
    sed -i "s/your-256-bit-secret-key-here/$JWT_SECRET/" .env
fi
echo "✓ JWT secret key generated"

# Check GPU availability
echo ""
echo "🎮 Checking GPU availability..."
python3 -c "
import sys
try:
    import torch
    if torch.cuda.is_available():
        print(f'✓ CUDA available: {torch.cuda.get_device_name(0)}')
        print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
    else:
        print('⚠️  CUDA not available. GPU acceleration disabled.')
except ImportError:
    print('⚠️  PyTorch not installed yet. GPU check skipped.')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env to configure your settings"
echo "  2. Run 'make docker-up' to start services with Docker"
echo "  3. Or run 'make dev' to start in development mode"
echo ""
echo "Documentation: https://github.com/your-org/axiom-engine/docs"
