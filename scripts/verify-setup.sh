#!/bin/bash

# MGX MVP Setup Verification Script

set -e

echo "================================================"
echo "MGX MVP - Setup Verification"
echo "================================================"
echo ""

# Check required files
echo "Checking required files..."
FILES=(
    "docker-compose.yml"
    ".env.example"
    "Makefile"
    "README.md"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/app/main.py"
    "frontend/Dockerfile"
    "frontend/package.json"
    "frontend/next.config.js"
    "infrastructure/nginx/nginx.conf"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        exit 1
    fi
done

echo ""
echo "All required files present!"
echo ""

# Check directory structure
echo "Checking directory structure..."
DIRS=(
    "backend/app"
    "frontend/src"
    "infrastructure/nginx/conf.d"
    "docs/design"
    "docs/project_management"
    "scripts"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/"
    else
        echo "❌ $dir/ (missing)"
        exit 1
    fi
done

echo ""
echo "All required directories present!"
echo ""

echo "================================================"
echo "Verification Complete!"
echo "================================================"
echo ""
echo "TASK-1.1 Status: ✅ COMPLETE"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure"
echo "2. Run 'make setup' to install dependencies"
echo "3. Run 'make docker-up' to start services"
echo ""