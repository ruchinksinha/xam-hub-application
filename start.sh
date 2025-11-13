#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "Starting Android Device Flashing Application..."

if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with LINEAGE_OS_URL variable"
    exit 1
fi

source .env

echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "Building frontend..."
npm run build

cd ..

echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi

echo "Installing Python dependencies..."
venv/bin/pip install -r backend/requirements.txt

echo "Starting backend server..."
echo "Application will be accessible at http://localhost"
echo "Press Ctrl+C to stop the server"
echo ""

sudo venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 80
