#!/bin/bash

# MGX MVP Build Script
# This script builds production images

set -e

echo "================================================"
echo "MGX MVP - Building Production Images"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run 'make setup' first."
    exit 1
fi

# Build backend image
echo "Building backend image..."
docker-compose build backend
echo "✅ Backend image built"

# Build frontend image
echo ""
echo "Building frontend image..."
docker-compose build frontend
echo "✅ Frontend image built"

# Build nginx image
echo ""
echo "Building nginx image..."
docker-compose build nginx
echo "✅ Nginx image built"

echo ""
echo "================================================"
echo "Build Complete!"
echo "================================================"
echo ""
echo "To start production services:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
echo ""