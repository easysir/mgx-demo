#!/bin/bash

# MGX MVP Development Script
# This script starts all services in development mode

set -e

echo "================================================"
echo "MGX MVP - Starting Development Environment"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run 'make setup' first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start Docker services
echo "Starting Docker services (PostgreSQL, Redis, Qdrant)..."
docker-compose up -d postgres redis qdrant

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 5

# Check PostgreSQL
echo "Checking PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U $POSTGRES_USER > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check Redis
echo "Checking Redis..."
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Check Qdrant
echo "Checking Qdrant..."
until curl -f http://localhost:6333/health > /dev/null 2>&1; do
    echo "Waiting for Qdrant..."
    sleep 2
done
echo "✅ Qdrant is ready"

# Run database migrations
echo ""
echo "Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
deactivate
cd ..
echo "✅ Database migrations complete"

# Start backend in background
echo ""
echo "Starting backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
deactivate
cd ..
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start frontend in background
echo ""
echo "Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "================================================"
echo "Development Environment Started!"
echo "================================================"
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Qdrant: http://localhost:6333"
echo ""
echo "Process IDs:"
echo "  - Backend: $BACKEND_PID"
echo "  - Frontend: $FRONTEND_PID"
echo ""
echo "To stop all services:"
echo "  - Press Ctrl+C"
echo "  - Or run: kill $BACKEND_PID $FRONTEND_PID"
echo "  - Or run: make docker-down"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; echo 'Services stopped.'; exit 0" INT

# Keep script running
wait