.PHONY: help setup dev build test clean docker-up docker-down docker-logs migrate

# Default target
help:
	@echo "MGX MVP - Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Initial project setup (copy .env, install dependencies)"
	@echo "  make install-backend - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services in development mode"
	@echo "  make dev-backend    - Start backend only"
	@echo "  make dev-frontend   - Start frontend only"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Start all Docker containers"
	@echo "  make docker-down    - Stop all Docker containers"
	@echo "  make docker-restart - Restart all Docker containers"
	@echo "  make docker-logs    - Show Docker logs"
	@echo "  make docker-clean   - Remove all Docker containers and volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create a new migration"
	@echo "  make migrate-down   - Rollback last migration"
	@echo "  make db-seed        - Seed database with test data"
	@echo "  make db-reset       - Reset database (drop all tables and re-migrate)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make test-e2e       - Run E2E tests"
	@echo "  make coverage       - Generate test coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linters (backend + frontend)"
	@echo "  make lint-backend   - Run backend linter (flake8, black, mypy)"
	@echo "  make lint-frontend  - Run frontend linter (eslint, prettier)"
	@echo "  make format         - Format code (backend + frontend)"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build          - Build production images"
	@echo "  make build-backend  - Build backend image"
	@echo "  make build-frontend - Build frontend image"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean temporary files and caches"
	@echo "  make clean-all      - Clean everything (including Docker volumes)"

# Setup & Installation
setup:
	@echo "Setting up MGX MVP..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@make install-backend
	@make install-frontend
	@echo "Setup complete! Run 'make dev' to start development."

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Development
dev:
	@echo "Starting all services..."
	docker-compose up

dev-backend:
	@echo "Starting backend only..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend only..."
	cd frontend && npm run dev

# Docker
docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-restart:
	@echo "Restarting Docker containers..."
	docker-compose restart

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

docker-clean:
	@echo "Cleaning Docker containers and volumes..."
	docker-compose down -v
	docker system prune -f

# Database
migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

migrate-down:
	@echo "Rolling back last migration..."
	cd backend && alembic downgrade -1

db-seed:
	@echo "Seeding database..."
	cd backend && python scripts/seed_db.py

db-reset:
	@echo "Resetting database..."
	cd backend && alembic downgrade base
	cd backend && alembic upgrade head
	@make db-seed

# Testing
test:
	@echo "Running all tests..."
	@make test-backend
	@make test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v --cov=app --cov-report=html

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm run test

test-e2e:
	@echo "Running E2E tests..."
	cd frontend && npm run test:e2e

coverage:
	@echo "Generating coverage report..."
	cd backend && pytest tests/ --cov=app --cov-report=html
	@echo "Coverage report generated at backend/htmlcov/index.html"

# Code Quality
lint:
	@echo "Running linters..."
	@make lint-backend
	@make lint-frontend

lint-backend:
	@echo "Running backend linters..."
	cd backend && flake8 app/ tests/
	cd backend && black --check app/ tests/
	cd backend && mypy app/

lint-frontend:
	@echo "Running frontend linters..."
	cd frontend && npm run lint

format:
	@echo "Formatting code..."
	cd backend && black app/ tests/
	cd backend && isort app/ tests/
	cd frontend && npm run format

# Build & Deploy
build:
	@echo "Building production images..."
	docker-compose build

build-backend:
	@echo "Building backend image..."
	docker-compose build backend

build-frontend:
	@echo "Building frontend image..."
	docker-compose build frontend

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +

clean-all:
	@make clean
	@make docker-clean
	@echo "All cleaned!"