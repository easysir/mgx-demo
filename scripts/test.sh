#!/bin/bash

# MGX MVP Test Script
# This script runs all tests

set -e

echo "================================================"
echo "MGX MVP - Running Tests"
echo "================================================"
echo ""

# Backend tests
echo "Running backend tests..."
cd backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=html --cov-report=term
deactivate
cd ..
echo "✅ Backend tests passed"

# Frontend tests
echo ""
echo "Running frontend tests..."
cd frontend
npm run test
cd ..
echo "✅ Frontend tests passed"

echo ""
echo "================================================"
echo "All Tests Passed!"
echo "================================================"
echo ""
echo "Coverage reports:"
echo "  - Backend: backend/htmlcov/index.html"
echo "  - Frontend: frontend/coverage/index.html"
echo ""