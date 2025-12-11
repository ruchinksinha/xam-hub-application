#!/bin/bash

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
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ ! -f "venv/bin/pip" ]; then
        echo "Error: Failed to create virtual environment - pip not found"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi

echo "Installing Python dependencies..."
venv/bin/pip install -r backend/requirements.txt

echo "Starting backend server on port 8000..."
echo "API will be accessible at http://localhost:8000"
echo "Frontend will be accessible at http://localhost (via nginx)"
echo "Press Ctrl+C to stop the server"
echo ""

venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
