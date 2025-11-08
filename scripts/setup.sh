#!/bin/bash

# MGX MVP Setup Script
# This script sets up the development environment

set -e

echo "================================================"
echo "MGX MVP - Setup Script"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please update the following in .env:"
    echo "   - JWT_SECRET_KEY (use: openssl rand -hex 32)"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GITHUB_TOKEN"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker is installed"

# Check Docker Compose
echo "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose is installed"

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION is installed"

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION is installed"

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo "✅ Backend dependencies installed"

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p backend/app/models
mkdir -p backend/app/api/v1
mkdir -p backend/app/core/session
mkdir -p backend/app/core/llm
mkdir -p backend/app/core/tools
mkdir -p backend/app/core/sandbox
mkdir -p backend/app/core/preview
mkdir -p backend/app/agents
mkdir -p backend/app/tasks
mkdir -p backend/app/middleware
mkdir -p backend/app/utils/security
mkdir -p backend/scripts
mkdir -p backend/tests
mkdir -p frontend/src/components/layout
mkdir -p frontend/src/components/chat
mkdir -p frontend/src/components/editor
mkdir -p frontend/src/components/preview
mkdir -p frontend/src/lib/websocket
mkdir -p frontend/src/store
mkdir -p infrastructure/nginx/conf.d
mkdir -p infrastructure/docker
echo "✅ Directories created"

# Generate JWT secret
echo ""
echo "Generating JWT secret..."
JWT_SECRET=$(openssl rand -hex 32)
echo "Generated JWT_SECRET_KEY: $JWT_SECRET"
echo "Please add this to your .env file"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys and secrets"
echo "2. Run 'make docker-up' to start all services"
echo "3. Run 'make migrate' to initialize the database"
echo "4. Visit http://localhost:3000 for the frontend"
echo "5. Visit http://localhost:8000/docs for the API docs"
echo ""
echo "For more commands, run 'make help'"
echo ""